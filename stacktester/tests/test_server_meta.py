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


class ServersMetadataTest(unittest.TestCase):

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
                'metadata' : {
                    'testEntry' : 'testValue'
                }
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)

        data = json.loads(body)
        self.server_id = data['server']['id']
    
    @classmethod
    def tearDownClass(self):
        self.os.nova.request('DELETE', '/servers/%s' % self.server_id)

    def test_get_servers_metadata(self):
        """Test that we can retrieve metadata for a server"""

        response, body = self.os.nova.request(
            'GET', '/servers/%s/meta' % self.server_id)
        result = json.loads(body)['metadata']
        self.assertEqual(result['testEntry'], 'testValue')

    def test_add_servers_metadata(self):
        """Test that we can add metadata to a server"""

        expected_meta = {'new_meta1' : 'new_value1', 'new_meta2' : 'new_value2'}

        put_body = json.dumps({
            'server' : {
                'metadata' : expected_meta
            }
        })

        response, body = self.os.nova.request(
            'PUT', '/servers/%s' % self.server_id, body=put_body)
        self.assertEqual(204, response.status)

        response, body = self.os.nova.request(
            'GET', '/servers/%s/meta' % self.server_id)
        metadata = json.loads(body)['metadata']
        self.assertDictEqual(expected_meta, metadata)

    def test_update_servers_metadata(self):
        """Test that we can update metadata for a server"""

        response, body = self.os.nova.request(
            'GET', '/servers/%s/meta' % self.server_id)
        result = json.loads(body)['metadata']
        self.assertEqual(result['testEntry'], 'testValue')
