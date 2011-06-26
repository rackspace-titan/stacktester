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

import stacktester
from stacktester import exceptions
from stacktester import openstack

import json
import unittest2 as unittest

SERVER_FIXTURES = [
    {
        'server' : {
            'name' : 'testserver',
            'imageRef' : 3,
            'flavorRef' : 1,
        }
    },
]

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


class ServersTest(unittest.TestCase):

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
                'imageRef' : 3,
                'flavorRef' : 1
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        
        data = json.loads(body)
        print body
        self.server_id = data['server']['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')


    def tearDown(self):
        for image in self.images.itervalues():
            self.os.glance.delete_image(image['id'])
        self.os.nova.request('DELETE', '/servers/%s' % self.server_id)

    def test_soft_reboot_server(self):
        """Verify a server can be rebooted with the soft option"""

        post_body = json.dumps({
            'reboot' : {
                'type' : 'SOFT'
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('202', response['status'])
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def test_hard_reboot_server(self):
        """ Verify a server can be rebooted with the hard option """

        post_body = json.dumps({
            'reboot' : {
                'type' : 'HARD'
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers/%s/action' % self.server_id, body=post_body)
        self.assertEqual('202', response['status'])
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

#    def test_resize_server_confirm(self):
#        
#        post_body = json.dumps({
#            'resize' : {
#                'flavor' : {
#                    'flavorRef': 2                
#                }
#            }
#        })
#
#        response, body = self.os.nova.request(
#            'POST', '/servers/%s/action' % self.server_id, body=post_body)
#        self.assertEqual('202', response['status'])
#        self.os.nova.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')
#
#        post_body = json.dumps({
#            'confirmResize' : 'null'
#        })
#
#        response, body = self.os.nova.request(
#            'POST', '/servers/%s/action' % self.server_id, body=post_body)
#        self.assertEqual('204', response['status'])
#        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')
