
import json
import os

import unittest2 as unittest

from stacktester import openstack
from stacktester import exceptions


class ServerAddressesTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.os = openstack.Manager()
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

    def setUp(self):
        server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
        }

        created_server = self.os.nova.create_server(server)
        self.server_id = created_server['id']
        self.os.nova.wait_for_server_status(self.server_id, 'ACTIVE')

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)

    def test_list_addresses(self):
        """Ensure address information is available"""
        url = '/servers/%s' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response.status, 200)
        _body = json.loads(body)
        self.assertTrue('addresses' in _body['server'].keys())
        # KNOWN-ISSUE lp761652
        #self.assertEqual(_body['server']['addresses'].keys(), ['private'])

        url = '/servers/%s/ips' % self.server_id
        response, body = self.os.nova.request('GET', url)
        # KNOWN-ISSUE lp761652
        #self.assertEqual(response.status, 200)
        #_body = json.loads(body)
        #self.assertEqual(_body.keys(), ['addresses'])
        #self.assertEqual(_body['addresses'].keys(), ['private'])

        url = '/servers/%s/ips/private' % self.server_id
        response, body = self.os.nova.request('GET', url)
        # KNOWN-ISSUE lp761652
        #self.assertEqual(response.status, 200)
        #_body = json.loads(body)
        #self.assertEqual(_body.keys(), ['private'])
