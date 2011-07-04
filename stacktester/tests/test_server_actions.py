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

from stacktester import exceptions
from stacktester import openstack

import unittest2 as unittest


class ServerActionsTest(unittest.TestCase):

    multi_node = openstack.Manager().config.env.multi_node

    def setUp(self):
        self.os = openstack.Manager()

        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

        expected_server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
        }

        server = self.os.nova.create_server(expected_server)

        self.server_id = server['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def test_reboot_server_soft(self):
        """Soft-reboot a specific server"""

        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT',
            }
        })

        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')

        #verify state change
        # KNOWN-ISSUE lp?
        #self.os.nova.wait_for_server_status(self.server_id, 'REBOOT')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def test_reboot_server_hard(self):
        """Hard-reboot a specific server"""

        post_body = json.dumps({
            'reboot' : {
                'type' : 'HARD',
            }
        })

        url = "/servers/%s/action" % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(response['status'], '202')

        #verify state change
        # KNOWN-ISSUE lp?
        #self.os.nova.wait_for_server_status(self.server_id, 'HARD_REBOOT')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

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

        #TODO: SSH into server using new password

    @unittest.skipIf(not multi_node, 'Multiple compute nodes required')
    def test_rebuild_server(self):
        """Rebuild a server from a different image"""
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
