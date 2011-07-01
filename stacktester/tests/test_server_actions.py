# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import json

from stacktester import openstack

import paramiko
import unittest2 as unittest


class ServerRebootActionTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
                'adminPass' : "testpwd",
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        # KNOWN-ISSUE lp802621
        #self.assertEqual('202', response['status'])

        data = json.loads(body)

        self.server_id = data['server']['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        
        response, body = self.os.nova.request(
            'GET', '/servers/%s' % self.server_id, body=post_body)
        #self.assertEqual('200', response['status'])

        data = json.loads(body)
        #current impl
        self.access_ip = data['server']['addresses']['private'][0]['addr']
        #current Spec
        #self.access_ip = data['server']['accessIPv4']

    @classmethod
    def tearDownClass(self):
        delete_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
            }
        })
        response, body = self.os.nova.request(
            'DELETE',
            '/servers/%s' % self.server_id,
            body=delete_body)
        #self.assertEqual('204', response['status'])

    def _get_uptime(self):
        
        ssh = paramiko.SSHClient()
        ssh.connect(self.access_ip, username='root', 
            password='testpwd')

        stdin, stdout, stderr = ssh.exec_command("cat /proc/uptime")
        uptime = int(stdout.read().split().pop(0))
        ssh.close()
        print uptime
        return uptime

    def test_reboot_server(self):
        """
        Verify that a server can be rebooted
        """

        #ssh and get the uptime
        initial_uptime = self._get_uptime()


        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT',
            }
        })


        response, body = self.os.nova.request(
            'POST', "/servers/%s/action" % self.server_id, body=post_body)
        self.assertEqual(response['status'], '202')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        #TODO ssh and verify uptime is less than before
        post_reboot_uptime = self._get_uptime()
        self.assertTrue(initial_uptime > post_reboot_uptime)

    def test_reboot_server_hard(self):
        """
        Verify that a server can be rebooted
        """

        post_body = json.dumps({
            'reboot' : {
                'type' : 'HARD',
            }
        })

        response, body = self.os.nova.request(
            'POST', "/servers/%s/action" % self.server_id, body=post_body)
        self.assertEqual(response['status'], '202')

        #TODO ssh and verify uptime is less than before


class ServerActionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
                'adminPass' : "testpwd",
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        # KNOWN-ISSUE lp802621
        #self.assertEqual('202', response['status'])

        data = json.loads(body)

        self.server_id = data['server']['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    @classmethod
    def tearDownClass(self):
        delete_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
            }
        })
        response, body = self.os.nova.request(
            'DELETE',
            '/servers/%s' % self.server_id,
            body=delete_body)
        #self.assertEqual('204', response['status'])

    def test_change_server_password(self):
        """Verify the root password of a server can be changed"""

        post_body = json.dumps({
            'changePassword' : {
                'adminPass' : 'test123'
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

        #TODO: SSH into server using new password
