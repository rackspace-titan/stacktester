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

import unittest2 as unittest

from stacktester import openstack


class ServersTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

    def test_list_empty_servers(self):
        """
        Verify that empty servers list works properly
        """

        response, body = self.os.nova.request('GET', '/servers')
        self.assertEqual(200, response.status)
        data = json.loads(body)
        self.assertTrue(not data['servers'])

    def test_create_delete_server(self):
        """
        Verify that a server instance can be created and deleted
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
            }
        })

        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        data = json.loads(body)
        server_id = data['server']['id']

        # KNOWN-ISSUE lp796742
        #self.assertEqual(202, resp.status) self.os.nova.wait_for_server_status(server_id, 'ACTIVE')

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
                'imageRef' : self.image_ref,
                'flavorRef' : self.flavor_ref,
            }
        })

        # Create Server
        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        # KNOWN-ISSUE lp796742
        #self.assertEqual(202, resp.status)

        data = json.loads(body)
        self.assertTrue('testserver', data['server']['name'])
        server_id = data['server']['id']

        # Wait for it to be created
        self.os.nova.wait_for_server_status(server_id, 'ACTIVE')

        # Update name
        put_body = json.dumps({
            'server' : {
                'name' : 'updatedtestserver'
            }
        })
        resp, body = self.os.nova.request(
            'PUT', '/servers/%s' % server_id, body=put_body)

        self.assertEqual(204, resp.status)

        # Get Server information
        resp, body = self.os.nova.request('GET', '/servers/%s' % server_id)

        self.assertEqual(200, resp.status)
        data = json.loads(body)
        self.assertEqual('updatedtestserver', data['server']['name'])

    def test_create_server_invalid_image(self):
        """
        Verify that creating a server with an unknown image ref will fail
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : -1,
                'flavorRef' : self.flavor_ref,
            }
        })

        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        self.assertTrue(400, resp.status)

    def test_create_server_invalid_flavor(self):
        """
        Verify that creating a server with an unknown image ref will fail
        """

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : -1,
            }
        })

        resp, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        self.assertTrue(400, resp.status)
