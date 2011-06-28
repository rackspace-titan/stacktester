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

#import random
#import time
#
import stacktester
from stacktester import openstack

import json
import unittest2 as unittest
#
IMAGE_FIXTURES = [
    {
        'name': 'ramdisk',
        'disk_format': 'ari',
        'container_format': 'ari',
        'is_public': True,
    },
    {
        'name': 'kernel',
        'disk_format': 'aki',
        'container_format': 'aki',
        'is_public': True,
    },
    {
        'name': 'image',
        'disk_format': 'ami',
        'container_format': 'ami',
        'is_public': True,
    },
]


class ServerActionsTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()
        self.config = stacktester.config.StackConfig()

        self.images = {}
        for IMAGE_FIXTURE in IMAGE_FIXTURES:
            IMAGE_FIXTURE['location'] = self.config.glance.get(
                '%s_uri' % IMAGE_FIXTURE['disk_format'], 'Invalid')
            meta = self.os.glance.add_image(IMAGE_FIXTURE, None)
            self.images[meta['name']] = {'id': meta['id']}

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.images['image']['id'],
                'flavorRef' : 3,
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        #self.assertEqual('202', response['status'])

        data = json.loads(body)

        self.server_id = data['server']['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def tearDown(self):
        for image in self.images.itervalues():
            self.os.glance.delete_image(image['id'])

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.images['image']['id'],
                'flavorRef' : 3,
            }
        })
        response, body = self.os.nova.request(
            'DELETE',
            '/servers/%s' % self.server_id,
            body=body)

#    def test_rebuild_server(self):
#        """
#        Test that a server can be rebuilt with a new image
#        """
#
#        self.server.rebuild("http://glance1:9292/v1/images/4")
#        self.server.waitForStatus('ACTIVE')
#        rebuilt_server = self.os.servers.get(self.server)
#        #TODO: let's assert something here
#
#
#    def test_resize_server_confirm(self):
#        """
#        Verify the flavor of a server can be changed
#        """
#
#        #Resize the server and wait for the action to finish
#        new_flavor = self.os.flavors.get(2)
#        self.server.resize(2)
#
#        #Confirm the resize
#        self.server.confirm_resize()
#
#        #Verify that the server's flavor has changed
#        modified_server = self.os.servers.get(self.server)
#        self.assertEqual(new_flavor.name, modified_server.flavorId)
#
#    def test_resize_server_revert(self):
#        """
#        Verify that a re-sized server can be reverted back to its
#        original flavor
#        """
#
#        # Resize the server and wait for it to finish
#        new_flavor = self.os.flavors.get(3)
#        self.server.resize(3)
#
#        #TODO: Not checking state at the moment because this test would hang
#
#        # Revert the resize
#        self.server.revert_resize()
#
#        # Check that the was reverted to its original flavor
#        modified_server = self.os.servers.get(server)
#        self.assertEqual(new_flavor.name, modified_server.flavorId)
#

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
        self.assertEqual(response['status'], '200')

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
        self.assertEqual(response['status'], '200')

        #verify state change
        self.os.nova.wait_for_server_status(self.server_id, 'HARD_REBOOT')
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
