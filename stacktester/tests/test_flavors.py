

from stacktester import openstack

import json
import unittest2 as unittest


class FlavorsTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()

    def tearDown(self):
        pass

    def _get_flavors(self):
        url = '/flavors'
        response, body = self.os.nova.request('GET', url)
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
            response, body = self.os.nova.request('GET', url)
            self.assertEqual(response['status'], '200')
            body_dict = json.loads(body)

            #Make sure result looks like a flavor
            self.assertTrue(body_dict.has_key('flavor'))

            actual = body_dict['flavor']

            self.assertTrue(actual.has_key('name'))
            self.assertTrue(actual.has_key('id'))
            self.assertTrue(actual.has_key('ram'))
            self.assertTrue(actual.has_key('disk'))

    def test_get_flavors(self):
        """
        Verify the expected flavors are returned
        """

        url = '/flavors'
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response['status'], '200')
        body_dict = json.loads(body)

        #Make sure result looks like a list of flavors
        self.assertTrue(body_dict.has_key('flavors'))

        flavors = json.loads(body)['flavors']
        for flavor in flavors:
            self.assertTrue(flavor.has_key('name'))
            self.assertTrue(flavor.has_key('id'))

    def test_get_flavors_detail(self):
        """
        Verify the detailed expected flavors are returned
        """

        url = '/flavors/detail'
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(response['status'], '200')
        body_dict = json.loads(body)

        #Make sure result looks like a list of flavors
        self.assertTrue(body_dict.has_key('flavors'))

        flavors = json.loads(body)['flavors']
        for flavor in flavors:
            self.assertTrue(flavor.has_key('name'))
            self.assertTrue(flavor.has_key('id'))
            self.assertTrue(flavor.has_key('ram'))
            self.assertTrue(flavor.has_key('disk'))
