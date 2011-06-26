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

class ServersMetadataTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()
        self.config = stacktester.config.StackConfig()

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : 3,
                'flavorRef' : 1,
                'metadata' : {
                    'testEntry' : 'testValue'
                }
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        
        data = json.loads(body)

        self.server_id = data['server']['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')


    def tearDown(self):
        self.os.nova.request('DELETE', '/servers/%s' % self.server_id)

    def test_get_servers_metdata(self):
        """Test that we can retrieve metadata for a server"""

        response, body = self.os.nova.request('GET', '/servers/%s/meta' % self.server_id)
        result = json.loads(body)['metadata']        
        self.assertEqual(result['testEntry'], 'testValue')

#    def test_add_server_metadata(self):
#        """Verify that key/value pairs can be added to a server's metadata"""
#
#        put_body = json.dumps({
#            'metadata' : {
#                'server label' : 'Web1',
#                'version' : '11.0'
#            }
#        })
#
#        response, body = self.os.nova.request(
#            'PUT', '/servers/%s/meta' % self.server_id, body=put_body)
#        
#        #self.assertEqual('201', response['status'])       
#        result = json.loads(body)['metadata']
#        self.assertEqual(result['server label'], 'Web1')
#        self.assertEqual(result['version'], '11.0')
#        if 'testEntry' in result: self.fail('This entry should be overwritten.')
#
#    def test_update_server_metadata(self):
#        """Verify that the metadata for a server can be updated"""
#    
#        post_body = json.dumps({
#            'metadata' : {
#                'key' : 'old'
#            }
#        })
#        response, body = self.os.nova.request(
#            'POST', '/servers/%s/meta' % self.server_id, body=post_body)
#        self.assertEqual('201', response['status'])
#        
#        post_body = json.dumps({
#            'metadata' : {
#                'key' : 'new'
#            }
#        })
#        response, body = self.os.nova.request(
#            'POST', '/servers/%s/meta' % self.server_id, body=post_body)
#        self.assertEqual('201', response['status'])
#        result = json.loads(body)['metadata']        
#        self.assertEqual(result['key'], 'new')
