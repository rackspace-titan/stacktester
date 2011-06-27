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

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.config = stacktester.config.StackConfig()

        self.images = {}
        for IMAGE_FIXTURE in IMAGE_FIXTURES:
            IMAGE_FIXTURE['location'] = self.config.glance.get(
                '%s_uri' % IMAGE_FIXTURE['disk_format'], 'Invalid')

            meta = self.os.glance.add_image(IMAGE_FIXTURE, None)
            self.images[meta['name']] = {'id': meta['id']}


    @classmethod
    def tearDownClass(self):
        for image in self.images.itervalues():
            self.os.glance.delete_image(image['id'])

    #def test_list_servers(self):
        #"""
        #Verify that a new server is returned in the list of
        #servers for the user
        #"""
        #serverList = self.os.servers.list()
        #found = False
        #for s in serverList:
            #if s.name == 'testserver':
                #found = True
        #assert found

    def test_create_delete_server(self):
        """
        Verify that a server instance can be created and deleted
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.images['image']['id'],
                'flavorRef' : 1,
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        data = json.loads(body)

        self.assertEqual('202', response['status'])
        server_id = data['server']['id']
        self.os.nova.wait_for_server_status(serverid, 'ACTIVE')

        self.assertEqual('testserver', data['server']['name'])

        response, body = self.os.nova.request(
            'DELETE',
            '/servers/%s' % server_id,
            body=body)

        # Raises TimeOutException on failure
        self.os.nova.poll_request_status('GET', '/servers/%s' % server_id, 404)

    def test_update_server_name(self):
        """
        Verify the name of an instance can be changed
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.images['image']['id'],
                'flavorRef' : 1,
            }
        })

        # Create Server
        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        self.assertEqual(resp['status'], '202')
        data = json.loads(body)
        serverid = data['server']['id']
        self.assertTrue(data['server']['name'], 'testserver')

        # Wait for it to be created
        self.os.nova.wait_for_server_status(serverid, 'ACTIVE')

        # Update name
        put_body = json.dumps({
            'server' : {
                'name' : 'updatedtestserver'
            }
        })
        resp, body = self.os.nova.request(
            'PUT', '/servers/%s' % serverid, body=put_body)

        self.assertEqual(resp['status'], '204')

        # Get Server information
        resp, body = self.os.nova.request('GET', '/servers/%s' % serverid)

        self.assertEqual(resp['status'], '202')
        data = json.loads(body)
        self.assertEqual(data['server']['name'], 'updatedtestserver')

    def test_create_server_invalid_image(self):
        """
        Verify that creating a server with an unknown image ref will fail
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : -3,
                'flavorRef' : 1,
            }
        })

        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        self.assertTrue(resp['status'], '400')

    def test_create_server_invalid_flavor(self):
        """
        Verify that creating a server with an unknown image ref will fail
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.images['image']['id'],
                'flavorRef' : -1,
            }
        })

        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        self.assertTrue(resp['status'], '400')
