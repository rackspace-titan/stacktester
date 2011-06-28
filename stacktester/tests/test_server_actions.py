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

import unittest2 as unittest


class ServerActionsTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()
        self.config = stacktester.config.StackConfig()
        #TODO get values from config
        self.image_ref = 3
        self.flavor_ref = 1

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        # KNOWN-ISSUE lp802621
        #self.assertEqual('202', response['status'])

        data = json.loads(body)

        self.server_id = data['server']['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def tearDown(self):
        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
            }
        })
        response, body = self.os.nova.request(
            'DELETE',
            '/servers/%s' % self.server_id,
            body=body)
        self.assertEqual('204', response['status'])

    def test_reboot_server(self):
        """
        Verify that a server can be rebooted
        """

        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT',
            }
        })

        response, body = self.os.nova.request(
            'POST', "/servers/%s/action" % self.server_id, body=post_body)
        self.assertEqual(response['status'], '202')

        #verify state change
        self.os.nova.wait_for_server_status(self.server_id, 'REBOOT')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

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

        #verify state change
        self.os.nova.wait_for_server_status(self.server_id, 'HARD_REBOOT')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

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
