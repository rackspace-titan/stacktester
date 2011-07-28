
import json
import time

from stacktester import exceptions
from stacktester import openstack
from stacktester.common import ssh

import unittest2 as unittest


class ServerActionsTest(unittest.TestCase):

    multi_node = openstack.Manager().config.env.multi_node

    def setUp(self):
        self.os = openstack.Manager()

        self.image_ref = self.os.config.env.image_ref
        self.image_ref_alt = self.os.config.env.image_ref_alt
        self.flavor_ref = self.os.config.env.flavor_ref
        self.flavor_ref_alt = self.os.config.env.flavor_ref_alt
        self.ssh_timeout = self.os.config.nova.ssh_timeout

        self.server_password = 'testpwd'
        self.server_name = 'testserver'

        expected_server = {
            'name' : self.server_name,
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
            'adminPass' : self.server_password,
        }

        created_server = self.os.nova.create_server(expected_server)

        self.server_id = created_server['id']
        self._wait_for_status(self.server_id, 'ACTIVE')

        server = self.os.nova.get_server(self.server_id)

        # KNOWN-ISSUE lp?
        #self.access_ip = server['accessIPv4']
        self.access_ip = server['addresses']['public'][0]['addr']

        # Ensure server came up
        self._assert_ssh_password()

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def _get_ssh_client(self, password):
        return ssh.Client(self.access_ip, 'root', password, self.ssh_timeout)

    def _assert_ssh_password(self, password=None):
        _password = password or self.server_password
        client = self._get_ssh_client(_password)
        self.assertTrue(client.test_connection_auth())

    def _wait_for_status(self, server_id, status):
        try:
            self.os.nova.wait_for_server_status(server_id, status)
        except exceptions.TimeoutException:
            self.fail("Server failed to change status to %s" % status)

    def _get_boot_time(self):
        """Return the time the server was started"""
        client = self._get_ssh_client(self.server_password)
        output = client.exec_command("cat /proc/uptime")
        uptime = float(output.split().pop(0))
        return time.time() - uptime

    def test_reboot_server_soft(self):
        """Verify that a server can be rebooted (SOFT)."""

        # SSH and get the uptime
        initial_time_started = self._get_boot_time()

        # Make reboot request
        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT',
            }
        })
        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')

        # Assert status transition
        self.os.nova.wait_for_server_status(self.server_id, 'REBOOT')
        ssh_client = self._get_ssh_client(self.server_password)
        ssh_client.connect_until_closed()
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        # SSH and verify uptime is less than before
        post_reboot_time_started = self._get_boot_time()
        self.assertTrue(initial_time_started < post_reboot_time_started)

    def test_reboot_server_hard(self):
        """Verify that a server can be rebooted (HARD)."""

        # SSH and get the uptime
        initial_time_started = self._get_boot_time()

        # Make reboot request
        post_body = json.dumps({
            'reboot' : {
                'type' : 'HARD',
            }
        })
        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')

        # Assert status transition
        self.os.nova.wait_for_server_status(self.server_id, 'HARD_REBOOT')
        ssh_client = self._get_ssh_client(self.server_password)
        ssh_client.connect_until_closed()
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        # SSH and verify uptime is less than before
        post_reboot_time_started = self._get_boot_time()
        self.assertTrue(initial_time_started < post_reboot_time_started)

    def test_change_server_password(self):
        """Change root password of a server"""

        # SSH into server using original password
        self._assert_ssh_password()

        # Change server password
        post_body = json.dumps({
            'changePassword' : {
                'adminPass' : 'test123',
            }
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Assert status transition
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'PASSWORD')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        # SSH into server using new password
        self._assert_ssh_password('test123')

    def test_rebuild_server(self):
        """Rebuild a server"""

        # Make rebuild request
        post_body = json.dumps({
            'rebuild' : {
                'imageRef' : self.image_ref_alt,
            }
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Ensure correct status transition
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'REBUILD')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        # Check that the instance's imageRef matches the new imageRef
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.image_ref_alt, server['imageRef'])

        # SSH into the server to ensure it came back up
        self._assert_ssh_password()

    @unittest.skipIf(not multi_node, 'Multiple compute nodes required')
    def test_resize_server_confirm(self):
        """Resize a server"""

        # Make resize request
        post_body = json.dumps({
            'resize' : {
                'flavorRef': self.flavor_ref_alt,
            }
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Wait for status transition
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'RESIZE')
        self.os.nova.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        # Ensure API reports new flavor
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavorRef'])

        #SSH into the server to ensure it came back up
        self._assert_ssh_password()

        # Make confirmResize request
        post_body = json.dumps({
            'confirmResize' : 'null'
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Wait for status transition
        self.assertEqual('204', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        # Ensure API still reports new flavor
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavorRef'])

    @unittest.skipIf(not multi_node, 'Multiple compute nodes required')
    def test_resize_server_revert(self):
        """Revert a server resize"""

        # Make resize request
        post_body = json.dumps({
            'resize' : {
                'flavorRef': self.flavor_ref_alt,
            }
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Wait for status transition
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'RESIZE')
        self.os.nova.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        # SSH into the server to ensure it came back up
        self._assert_ssh_password()

        # Ensure API reports new flavor
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref_alt, server['flavorRef'])

        # Make revertResize request
        post_body = json.dumps({
            'revertResize' : 'null'
        })
        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)

        # Assert status transition
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        # Ensure flavor ref was reverted to original
        server = self.os.nova.get_server(self.server_id)
        self.assertEqual(self.flavor_ref, server['flavorRef'])

