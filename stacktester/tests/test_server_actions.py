
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
        self.flavor_ref = self.os.config.env.flavor_ref
        self.ssh_timeout = self.os.config.nova.ssh_timeout

        expected_server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
            'adminPass' : "testpwd",
        }

        server = self.os.nova.create_server(expected_server)

        self.server_id = server['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE',
                                            timeout=300)

        response, body = self.os.nova.request(
            'GET', '/servers/%s' % self.server_id)
        self.assertEqual('200', response['status'])

        data = json.loads(body)
        #current impl
        self.access_ip = data['server']['addresses']['private'][0]['addr']
        #current Spec
        #self.access_ip = server['accessIPv4']
        self.ssh = ssh.Client(self.access_ip, 'root', 'testpwd', 300)

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def _wait_for_status(self, server_id, status):
        try:
            self.os.nova.wait_for_server_status(server_id, status)
        except exceptions.TimeoutException:
            self.fail("Server failed to change status to %s" % status)

    def _get_boot_time(self):
        """Return the time the server was started"""
        output = self.ssh.exec_command("cat /proc/uptime")
        uptime = float(output.split().pop(0))
        return time.time() - uptime

    def test_reboot_server_soft(self):
        """Verify that a server can be soft rebooted."""

        #ssh and get the uptime
        initial_time_started = self._get_boot_time()

        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT',
            }
        })

        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        self.ssh.connect_until_closed()
        #ssh and verify uptime is less than before
        post_reboot_time_started = self._get_boot_time()

        self.assertTrue(initial_time_started < post_reboot_time_started)

    def test_reboot_server_hard(self):
        """Verify that a server can be hard rebooted."""

        #ssh and get the uptime
        initial_time_started = self._get_boot_time()

        post_body = json.dumps({
            'reboot' : {
                'type' : 'HARD',
            }
        })

        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        self.ssh.connect_until_closed()
        #ssh and verify uptime is less than before
        post_reboot_time_started = self._get_boot_time()

        self.assertTrue(initial_time_started < post_reboot_time_started)

    def test_change_server_password(self):
        """Change root password of a server"""

        post_body = json.dumps({
            'changePassword' : {
                'adminPass' : 'test123'
            }
        })

        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        
        #SSH into server using new password
        new_pwd_ssh_client = ssh.Client(self.access_ip, 'root', 'test123', 180)
        self.assertTrue(new_pwd_ssh_client.test_connection_auth())

    @unittest.skipIf(not multi_node, 'Multiple compute nodes required')
    def test_rebuild_server(self):
        """Rebuild a server"""
        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : 2,
                'flavorRef' : self.flavor_ref,
            }
        })

        response, body = self.os.nova.request('POST','/servers', body=post_body)

        # KNOWN-ISSUE lp?
        # self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'REBUILD')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        #Check that the instance's imageRef matches the new imageRef
        resp, body = self.os.nova.request('GET', '/servers/%s' % self.server_id)
        data = json.loads(body)
        self.assertEqual(2, data['server']['imageRef'])

    @unittest.skipIf(not multi_node, 'Multiple compute nodes required')
    def test_resize_server_confirm(self):
        """Resize a server"""
        post_body = json.dumps({
            'resize' : {
                'flavorRef': 2
            }
        })

        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        post_body = json.dumps({
            'confirmResize' : 'null'
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('204', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        resp, body = self.os.nova.request('GET', '/servers/%s' % self.server_id)
        data = json.loads(body)
        self.assertEqual(2, data['server']['flavorRef'])

    @unittest.skipIf(not multi_node, 'Multiple compute nodes required')
    def test_resize_server_revert(self):
        """Revert a server resize"""

        post_body = json.dumps({
            'resize' : {
                'flavorRef': 2
            }
        })

        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')

        post_body = json.dumps({
            'revertResize' : 'null'
        })

        url = '/servers/%s/action' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        resp, body = self.os.nova.request('GET', '/servers/%s' % self.server_id)
        data = json.loads(body)
        self.assertEqual(self.flavor_ref, data['server']['flavorRef'])
