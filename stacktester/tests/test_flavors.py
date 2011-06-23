

from stacktester import openstack

import json
import unittest

#TODO: only for optional setup
FIXTURES = [
    {"flavorid": 1, "name": "m1.tiny", "ram": 512, "vcpus": 1, "disk": 0},
    {"flavorid": 2, "name": "m1.small", "ram": 2048, "vcpus": 1, "disk": 20},
] 


class FlavorsTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()

    def tearDown(self):
        pass

    def _get_flavors(self):
        url = '/flavors'
        response, body = self.os.nova_api.request('GET', url)
        self.assertEqual(response['status'], '200')
        flavors = json.loads(body)['flavors']
        return flavors

    def test_get_flavor_details(self):
        """
        Verify the expected details are returned for a flavor
        """

        flavors = self._get_flavors()

        for flavor in flavors:
            flavor_id = flavor['id']
            url = '/flavors/%s' % flavor_id
            response, body = self.os.nova_api.request('GET', url)
            self.assertEqual(response['status'], '200')
            body_dict = json.loads(body)

            #Make sure result looks like a flavor
            has_flavor_in_response = body_dict.has_key('flavor')
            self.assertTrue(has_flavor_in_response)
            
            if has_flavor_in_response:
                actual = json.loads(body)['flavor']

                self.assertTrue(actual.has_key('name'))
                self.assertTrue(flavor.has_key('id'))
                self.assertTrue(actual.has_key('ram'))
                self.assertTrue(actual.has_key('disk'))

    def test_get_flavors(self):
        """
        Verify the expected flavors are returned
        """

        url = '/flavors'
        response, body = self.os.nova_api.request('GET', url)
        self.assertEqual(response['status'], '200')
        body_dict = json.loads(body)

        #Make sure result looks like a list of flavors
        has_flavors_in_response = body_dict.has_key('flavors')
        self.assertTrue(has_flavors_in_response)
        
        if has_flavors_in_response:
            flavors = json.loads(body)['flavors']
            for flavor in flavors:
                self.assertTrue(flavor.has_key('name'))
                self.assertTrue(flavor.has_key('id'))

    def test_get_flavors_detail(self):
        """
        Verify the detailed expected flavors are returned
        """

        url = '/flavors/detail'
        response, body = self.os.nova_api.request('GET', url)
        self.assertEqual(response['status'], '200')
        body_dict = json.loads(body)

        #Make sure result looks like a list of flavors
        has_flavors_in_response = body_dict.has_key('flavors')
        self.assertTrue(has_flavors_in_response)
        
        if has_flavors_in_response:
            flavors = json.loads(body)['flavors']
            for flavor in flavors:
                self.assertTrue(flavor.has_key('name'))
                self.assertTrue(flavor.has_key('id'))
                self.assertTrue(flavor.has_key('ram'))
                self.assertTrue(flavor.has_key('disk'))
