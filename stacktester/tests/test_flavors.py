

from stacktester import openstack

import unittest


class FlavorsTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()

    def test_get_flavor_details(self):
        """Verify the expected details are returned for a flavor."""
        response, body = self.os.nova_api.request('GET', '/flavors/1')
        self.assertEqual(response['status'], '200')
