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
import socket 
import time

from stacktester import exceptions
from stacktester import openstack

import paramiko
import unittest2 as unittest


class ServerRebootActionTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref
        self.ssh_timeout = self.os.config.nova.ssh_timeout

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

    def _get_time_started(self):
        """Return the time the server was started"""
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        ssh.connect(self.access_ip, username='root', 
            password='testpwd', look_for_keys=False, timeout=300)

        stdin, stdout, stderr = ssh.exec_command("cat /proc/uptime")
        uptime = float(stdout.read().split().pop(0))
        ssh.close()
        print time.time() - uptime
        return time.time() - uptime

    def _connect_until_closed(self):
        """Return the time the server was started"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            ssh.connect(self.access_ip, username='root', 
                password='testpwd', look_for_keys=False,
                timeout=self.ssh_timeout)
            _transport = ssh.get_transport()
            while _transport.is_active():
                time.sleep(5)
            ssh.close()
        except EOFError:
            return
        except socket.error:
            return

    def _wait_for_status(self, server_id, status):
        try:
            self.os.nova.wait_for_server_status(server_id, status)
        except exceptions.TimeoutException:
            self.fail("Server failed to change status to %s" % status)

    def test_reboot_server(self):
        """
        Verify that a server can be rebooted
        """

        time.sleep(20)
        #ssh and get the uptime
        initial_time_started = self._get_time_started()


        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT',
            }
        })


        response, body = self.os.nova.request(
            'POST', "/servers/%s/action" % self.server_id, body=post_body)
        self.assertEqual(response['status'], '202')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
        self._connect_until_closed()
        #TODO ssh and verify uptime is less than before
        post_reboot_time_started = self._get_time_started()
        self.assertTrue(initial_time_started < post_reboot_time_started)

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

    multi_node = openstack.Manager().config.env.multi_node

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
        self._wait_for_status(self.server_id, 'ACTIVE')

        #TODO: SSH into server using new password

    @unittest.skipIf(not multi_node, 'Test requires more than one compute node')
    def test_rebuild_server(self):
        """ 
        Verify that a server instance can be rebuilt using a different image 
        """
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
        self._wait_for_status(self.server_id, 'REBUILD')
        self._wait_for_status(self.server_id, 'ACTIVE')
        
        #Check that the instance's imageRef matches the new imageRef
        resp, body = self.os.nova.request('GET', '/servers/%s' % self.server_id)
        data = json.loads(body)        
        self.assertEqual(2, data['server']['imageRef'])   
    
    @unittest.skipIf(not multi_node, 'Test requires more than one compute node')
    def test_resize_server_confirm(self):
        """ Verify that a server can be resized """
        post_body = json.dumps({
            'resize' : {
                'flavorRef': 2                
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('202', response['status'])
        self._wait_for_status(self.server_id, 'VERIFY_RESIZE')

        post_body = json.dumps({
            'confirmResize' : 'null'
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('204', response['status'])
        self._wait_for_status(self.server_id, 'ACTIVE')
        resp, body = self.os.nova.request('GET', '/servers/%s' % self.server_id)
        data = json.loads(body)        
        self.assertEqual(2, data['server']['flavorRef'])

    @unittest.skipIf(not multi_node, 'Test requires more than one compute node')
    def test_resize_server_revert(self):
        """ Verify that a server resize can be reverted """
        
        post_body = json.dumps({
            'resize' : {
                'flavorRef': 2                
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('202', response['status'])
        self._wait_for_status(self.server_id, 'VERIFY_RESIZE')

        post_body = json.dumps({
            'revertResize' : 'null'
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('202', response['status'])
        self._wait_for_status(self.server_id, 'ACTIVE')
        resp, body = self.os.nova.request('GET', '/servers/%s' % self.server_id)
        data = json.loads(body)        
        self.assertEqual(self.flavor_ref, data['server']['flavorRef'])
