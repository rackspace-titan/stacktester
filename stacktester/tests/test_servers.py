
import json
import os

import unittest2 as unittest

from stacktester import openstack
from stacktester import exceptions


class ServersTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

    def _assert_server_entity(self, server):
        actual_keys = set(server.keys())
        expected_keys = set((
            'id',
            'name',
            'hostId',
            'status',
            'metadata',
            'addresses',
            'links',

            #KNOWN-ISSUE lp804093
            'uuid',

            #KNOWN-ISSUE lp804096
            #'created',
            #'updated',

            #KNOWN-ISSUE
            #'primaryIPv4',

            #KNOWN-ISSUE
            #'primaryIPv6',

            #KNOWN-ISSUE
            #'progress',

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'image',
            'imageRef',

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'flavor',
            'flavorRef',
        ))
        self.assertEqual(actual_keys, expected_keys)

        server_id = str(server['id'])
        host = self.os.config.nova.host
        port = self.os.config.nova.port
        api_url = '%s:%s' % (host, port)
        base_url = os.path.join(api_url, self.os.config.nova.base_url)

        self_link = 'http://' + os.path.join(base_url, 'servers', server_id)
        bookmark_link = 'http://' + os.path.join(api_url, 'servers', server_id)

        expected_links = [
            {
                'rel': 'self',
                'href': self_link,
            },
            {
                'rel': 'bookmark',
                'href': bookmark_link,
            },
        ]

        # KNOWN-ISSUE lp803505
        #self.assertEqual(server['links'], expected_links)

    def test_build_server(self):
        """Build a server"""

        expected_server = {
            'name': 'testserver',
            'metadata': {
                'key1': 'value1',
                'key2': 'value2',
            },
            'adminPass': 'my_password',

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'image': {'id': self.image_ref},
            'imageRef': self.image_ref,

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'flavor': {'id': self.flavor_ref},
            'flavorRef': self.flavor_ref,
        }

        post_body = json.dumps({'server': expected_server})
        response, body = self.os.nova.request('POST',
                                              '/servers',
                                              body=post_body)
        # KNOWN-ISSUE
        #self.assertEqual(response.status, 202)
        self.assertEqual(response.status, 200)

        _body = json.loads(body)
        self.assertEqual(_body.keys(), ['server'])
        created_server = _body['server']

        admin_pass = created_server.pop('adminPass', None)
        self._assert_server_entity(created_server)
        self.assertEqual(expected_server['name'], created_server['name'])
        self.assertEqual(expected_server['adminPass'], admin_pass)
        self.assertEqual(expected_server['metadata'],
                         created_server['metadata'])

        self.os.nova.wait_for_server_status(created_server['id'], 'ACTIVE')

        self.os.nova.delete_server(created_server['id'])

    def test_delete_server_building(self):
        """Delete a server while building"""

        server = {
            'name' : 'testserver',

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'image': {'id': self.image_ref},
            'imageRef' : self.image_ref,

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'flavor': {'id': self.flavor_ref},
            'flavorRef' : self.flavor_ref,
        }

        created_server = self.os.nova.create_server(server)

        # Server should immediately be accessible and building
        url = '/servers/%s' % created_server['id']
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response['status'], '200')
        resp_server = json.loads(body)['server']
        self.assertEqual(resp_server['status'], 'BUILD')

        self.os.nova.delete_server(created_server['id'])

        # Poll server until deleted
        try:
            url = '/servers/%s' % created_server['id']
            self.os.nova.poll_request_status('GET', url, 404)
        except exceptions.TimeoutException:
            self.fail("Server deletion timed out")

    def test_delete_server_active(self):
        """Delete a server after fully built"""

        expected_server = {
            'name' : 'testserver',

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'image': {'id': self.image_ref},
            'imageRef' : self.image_ref,

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'flavor': {'id': self.flavor_ref},
            'flavorRef' : self.flavor_ref,
        }

        created_server = self.os.nova.create_server(expected_server)
        server_id = created_server['id']

        self.os.nova.wait_for_server_status(server_id, 'ACTIVE')

        self.os.nova.delete_server(server_id)

        # Poll server until deleted
        try:
            url = '/servers/%s' % server_id
            self.os.nova.poll_request_status('GET', url, 404)
        except exceptions.TimeoutException:
            self.fail("Server deletion timed out")

    def test_update_server_name(self):
        """Change the name of a server"""

        expected_server = {
            'name' : 'testserver',

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'image': {'id': self.image_ref},
            'imageRef' : self.image_ref,

            #KNOWN-ISSUE - maybe spec will drop this requirement?
            #'flavor': {'id': self.flavor_ref},
            'flavorRef' : self.flavor_ref,
        }

        created_server = self.os.nova.create_server(expected_server)

        self.assertTrue(expected_server['name'], created_server['name'])
        server_id = created_server['id']

        # Wait for it to be built
        self.os.nova.wait_for_server_status(server_id, 'ACTIVE')

        # Update name
        new_server = {'name': 'updatedtestserver'}
        put_body = json.dumps({
            'server': new_server,
        })
        url = '/servers/%s' % server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

        self.assertEqual(resp.status, 204)
        self.assertEqual(body, '')

        # Get Server information
        resp, body = self.os.nova.request('GET', '/servers/%s' % server_id)
        self.assertEqual(200, resp.status)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual('updatedtestserver', data['server']['name'])

        self.os.nova.delete_server(server_id)

    def test_create_server_invalid_image(self):
        """Verify that creating a server with an unknown image fails"""

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',

                # KNOWN-ISSUE
                #'image': {'id': self.image_ref},
                'imageRef' : -1,

                # KNOWN-ISSUE
                #'flavor': {'id': self.flavor_ref},
                'flavorRef' : self.flavor_ref,
            }
        })

        resp, body = self.os.nova.request('POST', '/servers', body=post_body)

        self.assertEqual(400, resp.status)

        fault = json.loads(body)
        expected_fault = {
            "badRequest": {
                "message": "Cannot find requested image",
                "code": 400,
            },
        }
        # KNOWN-ISSUE - The error message is confusing and should be improved
        #self.assertEqual(fault, expected_fault)

    def test_create_server_invalid_flavor(self):
        """Verify that creating a server with an unknown flavor fails"""

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',

                # KNOWN-ISSUE
                #'image': {'id': self.image_ref},
                'imageRef' : self.image_ref,

                # KNOWN-ISSUE
                #'flavor': {'id': self.flavor_ref},
                'flavorRef' : -1,
            }
        })

        resp, body = self.os.nova.request('POST', '/servers', body=post_body)

        self.assertEqual(400, resp.status)

        # KNOWN-ISSUE lp804084
        #fault = json.loads(body)
        expected_fault = {
            "badRequest": {
                "message": "Cannot find requested flavor",
                "code": 400,
            },
        }
        #self.assertEqual(fault, expected_fault)
