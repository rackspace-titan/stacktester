
import base64
import json
import os

import unittest2 as unittest

from stacktester import openstack
from stacktester import exceptions
from stacktester.common import ssh


class ServersTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref
        self.ssh_timeout = self.os.config.nova.ssh_timeout
        self.build_timeout = self.os.config.nova.build_timeout

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
            'progress',
            'image',
            'flavor',
            'created',
            'updated',
            'accessIPv4',
            'accessIPv6',

            #KNOWN-ISSUE lp804093
            'uuid',

        ))
        self.assertTrue(expected_keys <= actual_keys)

        server_id = str(server['id'])
        host = self.os.config.nova.host
        port = self.os.config.nova.port
        api_url = '%s:%s' % (host, port)
        base_url = os.path.join(api_url, self.os.config.nova.base_url)

        self_link = 'http://' + os.path.join(base_url,
                                             self.os.config.nova.project_id,
                                             'servers', server_id)
        bookmark_link = 'http://' + os.path.join(api_url,
                                            self.os.config.nova.project_id,
                                            'servers', server_id)

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

        self.assertEqual(server['links'], expected_links)

    def test_build_server(self):
        """Build a server"""

        expected_server = {
            'name': 'testserver',
            'metadata': {
                'key1': 'value1',
                'key2': 'value2',
            },
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
        }

        post_body = json.dumps({'server': expected_server})
        response, body = self.os.nova.request('POST',
                                              '/servers',
                                              body=post_body)

        # Ensure attributes were returned
        self.assertEqual(response.status, 202)
        _body = json.loads(body)
        self.assertEqual(_body.keys(), ['server'])
        created_server = _body['server']
        admin_pass = created_server.pop('adminPass')
        self._assert_server_entity(created_server)
        self.assertEqual(expected_server['name'], created_server['name'])
        self.assertEqual(expected_server['metadata'],
                         created_server['metadata'])
        self.assertEqual(created_server['accessIPv4'], '')
        self.assertEqual(created_server['accessIPv6'], '')

        # Wait for instance to boot
        server_id = created_server['id']
        self.os.nova.wait_for_server_status(server_id,
                                            'ACTIVE',
                                            timeout=self.build_timeout)

        # Get server again and ensure attributes stuck
        server = self.os.nova.get_server(server_id)
        self._assert_server_entity(server)
        self.assertEqual(server['name'], expected_server['name'])
        self.assertEqual(server['metadata'], expected_server['metadata'])
        self.assertEqual(server['accessIPv4'], '')
        self.assertEqual(server['accessIPv6'], '')

        # Find IP of server
        try:
            (_, network) = server['addresses'].popitem()
            ip = network[0]['addr']
        except KeyError:
            self.fail("Failed to retrieve IP address from server entity")

        # Assert password works
        client = ssh.Client(ip, 'root', admin_pass, self.ssh_timeout)
        self.assertTrue(client.test_connection_auth())

        # Look for 'addresses' attribute on server
        url = '/servers/%s' % server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        body = json.loads(body)
        self.assertTrue('addresses' in body['server'].keys())
        server_addresses = body['server']['addresses']

        # Addresses should be available from subresource
        url = '/servers/%s/ips' % server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        body = json.loads(body)
        self.assertEqual(body.keys(), ['addresses'])
        ips_addresses = body['addresses']

        # Ensure both resources return identical information
        self.assertEqual(server_addresses, ips_addresses)

        # Validate entities within network containers
        for (network, network_data) in ips_addresses.items():
            url = '/servers/%s/ips/%s' % (server_id, network)
            response, body = self.os.nova.request('GET', url)
            self.assertEqual(response.status, 200)
            body = json.loads(body)
            self.assertEqual(body.keys(), [network])
            self.assertEqual(body[network], network_data)

            # Check each IP entity
            for ip_data in network_data:
                self.assertEqual(set(ip_data.keys()), set(['addr', 'version']))

        # Clean up server
        self.os.nova.delete_server(server['id'])

    def test_build_server_with_file(self):
        """Build a server with an injected file"""

        file_contents = 'testing'

        expected_server = {
            'name': 'testserver',
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
            'personality': [
                {
                    'path': '/etc/test.txt',
                    'contents': base64.b64encode(file_contents),
                },
            ],
        }

        post_body = json.dumps({'server': expected_server})
        response, body = self.os.nova.request('POST',
                                              '/servers',
                                              body=post_body)

        # Verify returned server entity
        self.assertEqual(response.status, 202)
        _body = json.loads(body)
        self.assertEqual(_body.keys(), ['server'])
        created_server = _body['server']
        admin_pass = created_server.pop('adminPass', None)
        self._assert_server_entity(created_server)
        self.assertEqual(expected_server['name'], created_server['name'])
        self.assertEqual(expected_server['metadata'],
                         created_server['metadata'])

        # Wait for instance to boot
        self.os.nova.wait_for_server_status(created_server['id'],
                                            'ACTIVE',
                                            timeout=self.build_timeout)

        server = self.os.nova.get_server(created_server['id'])
        self.assertTrue('adminPass' not in server)

        # Find IP of server
        try:
            (_, network) = server['addresses'].popitem()
            ip = network[0]['addr']
        except KeyError:
            self.fail("Failed to retrieve IP address from server entity")

        # Assert injected file is on instance, also verifying password works
        client = ssh.Client(ip, 'root', admin_pass, self.ssh_timeout)
        injected_file = client.exec_command('cat /etc/test.txt')
        self.assertEqual(injected_file, file_contents)

        # Clean up created server
        self.os.nova.delete_server(server['id'])

    def test_build_server_with_password(self):
        """Build a server with a password"""

        server_password = 'testpwd'

        expected_server = {
            'name': 'testserver',
            'imageRef': self.image_ref,
            'flavorRef': self.flavor_ref,
            'adminPass': server_password,
        }

        post_body = json.dumps({'server': expected_server})
        response, body = self.os.nova.request('POST',
                                              '/servers',
                                              body=post_body)

        # Check attributes on the returned entity
        self.assertEqual(response.status, 202)
        _body = json.loads(body)
        self.assertEqual(_body.keys(), ['server'])
        created_server = _body['server']
        admin_pass = created_server.pop('adminPass', None)
        self._assert_server_entity(created_server)
        self.assertEqual(expected_server['name'], created_server['name'])
        self.assertEqual(expected_server['adminPass'], admin_pass)
        self.assertEqual(expected_server['metadata'],
                         created_server['metadata'])

        # Wait for instance to boot
        self.os.nova.wait_for_server_status(created_server['id'],
                                            'ACTIVE',
                                            timeout=self.build_timeout)

        server = self.os.nova.get_server(created_server['id'])
        self.assertTrue('adminPass' not in server)

        # Find IP of server
        try:
            (_, network) = server['addresses'].popitem()
            ip = network[0]['addr']
        except KeyError:
            self.fail("Failed to retrieve IP address from server entity")

        # Assert password was set to that in request
        client = ssh.Client(ip, 'root', server_password, self.ssh_timeout)
        self.assertTrue(client.test_connection_auth())

        # Clean up created server
        self.os.nova.delete_server(server['id'])

    def test_delete_server_building(self):
        """Delete a server while building"""

        # Make create server request
        server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
        }
        created_server = self.os.nova.create_server(server)

        # Server should immediately be accessible, but in have building status
        server = self.os.nova.get_server(created_server['id'])
        self.assertEqual(server['status'], 'BUILD')

        self.os.nova.delete_server(created_server['id'])

        # Poll server until deleted
        try:
            url = '/servers/%s' % created_server['id']
            self.os.nova.poll_request_status('GET', url, 404)
        except exceptions.TimeoutException:
            self.fail("Server deletion timed out")

    def test_server_attribute_manipulation(self):
        """Modify the attributes of a server"""

        expected_server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
            'metadata' : {'testEntry' : 'testValue'},
        }

        # Don't block for the server to build
        created_server = self.os.nova.create_server(expected_server)

        self.assertTrue(expected_server['name'], created_server['name'])
        server_id = created_server['id']

        # Update name
        new_server = {'name': 'updatedtestserver'}
        put_body = json.dumps({'server': new_server})
        url = '/servers/%s' % server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

        # Output from update should be a full server
        self.assertEqual(resp.status, 200)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual('updatedtestserver', data['server']['name'])

        # Check that name was changed
        updated_server = self.os.nova.get_server(server_id)
        self._assert_server_entity(updated_server)
        self.assertEqual('updatedtestserver', updated_server['name'])

        # Update accessIPv4
        new_server = {'accessIPv4': '192.169.0.200'}
        put_body = json.dumps({'server': new_server})
        url = '/servers/%s' % server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

        # Output from update should be a full server
        self.assertEqual(resp.status, 200)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual('192.168.0.200', data['server']['accessIPv4'])

        # Check that accessIPv4 was changed
        updated_server = self.os.nova.get_server(server_id)
        self._assert_server_entity(updated_server)
        self.assertEqual('192.168.0.200', updated_server['accessIPv4'])

        # Update accessIPv6
        new_server = {'accessIPv6': 'feed::beef'}
        put_body = json.dumps({'server': new_server})
        url = '/servers/%s' % server_id
        resp, body = self.os.nova.request('PUT', url, body=put_body)

        # Output from update should be a full server
        self.assertEqual(resp.status, 200)
        data = json.loads(body)
        self.assertEqual(data.keys(), ['server'])
        self._assert_server_entity(data['server'])
        self.assertEqual('feed::beef', data['server']['accessIPv6'])

        # Check that accessIPv6 was changed
        updated_server = self.os.nova.get_server(server_id)
        self._assert_server_entity(updated_server)
        self.assertEqual('feed::beef', updated_server['accessIPv6'])

        # Ensure metadata is set on create
        expected = {'testEntry' : 'testValue'}
        self.assertEqual(expected, data['server']['metadata'])

        # Check metadata subresource
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)

        result = json.loads(body)
        expected = {
            'metadata' : {
                'testEntry' : 'testValue',
            },
        }
        self.assertEqual(expected, result)

        # Ensure metadata container can be modified
        post_metadata = {
            'metadata' : {
                'new_entry1' : 'new_value1',
                'new_entry2' : 'new_value2',
            },
        }
        post_body = json.dumps(post_metadata)
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        expected = post_metadata
        expected['metadata']['testEntry'] = 'testValue'
        self.assertEqual(expected, result)

        # Ensure values stick
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        expected = post_metadata
        expected['metadata']['testEntry'] = 'testValue'
        self.assertEqual(expected, result)

        # Ensure metadata container can be overwritten
        expected = {
            'metadata' : {
                'new_entry3' : 'new_value3',
                'new_entry4' : 'new_value4',
            },
        }
        url = '/servers/%s/metadata' % self.server_id
        post_body = json.dumps(expected)
        response, body = self.os.nova.request('PUT', url, body=post_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        expected = post_metadata
        self.assertEqual(expected, result)

        # Ensure values stick
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected, result)

        # Set specific key
        expected_meta = {'meta' : {'new_meta5' : 'new_value5'}}
        put_body = json.dumps(expected_meta)
        url = '/servers/%s/metadata/new_meta5' % self.server_id
        response, body = self.os.nova.request('PUT', url, body=put_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertDictEqual(expected_meta, result)

        # Ensure value sticks
        expected_metadata = {
            'metadata' : {
                'new_meta3' : 'new_value3',
                'new_meta4' : 'new_value4',
                'new_meta5' : 'new_value5',
            },
        }
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        result = json.loads(body)
        self.assertDictEqual(expected_metadata, result)

        # Update existing key
        expected_meta = {'meta' : {'new_meta4' : 'new_meta6'}}
        put_body = json.dumps(expected_meta)
        url = '/servers/%s/metadata/new_meta4' % self.server_id
        response, body = self.os.nova.request('PUT', url, body=put_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected_meta, result)

        # Ensure value sticks
        expected_metadata = {
            'metadata' : {
                'new_meta3' : 'new_value3',
                'new_meta4' : 'new_value6',
                'new_meta5' : 'new_value5',
            },
        }
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        result = json.loads(body)
        self.assertDictEqual(expected_metadata, result)

        # Delete a certain key
        url = '/servers/%s/metadata/new_meta3' % self.server_id
        response, body = self.os.nova.request('DELETE', url)
        self.assertEquals(204, response.status)

        # Make sure the key is gone
        url = '/servers/%s/metadata/new_meta3' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEquals(404, response.status)

        # Delete a nonexistant key
        url = '/servers/%s/metadata/new_meta3' % self.server_id
        response, body = self.os.nova.request('DELETE', url)
        self.assertEquals(404, response.status)

    def test_create_server_invalid_image(self):
        """Create a server with an unknown image"""

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : -1,
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
        """Create a server with an unknown flavor"""

        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.image_ref,
                'flavorRef' : -1,
            }
        })

        resp, body = self.os.nova.request('POST', '/servers', body=post_body)

        self.assertEqual(400, resp.status)

        fault = json.loads(body)
        expected_fault = {
            "badRequest": {
                "message": "Cannot find requested flavor",
                "code": 400,
            },
        }
        # KNOWN-ISSUE lp804084
        #self.assertEqual(fault, expected_fault)
