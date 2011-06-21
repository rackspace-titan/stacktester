
from stacktester import openstack

import json
import unittest


FIXTURES = [
    {
        'name': 'Image1',
        'disk_format': 'vdi',
        'container_format': 'ovf',
    },
]


class ImagesTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()
        self.images = {}
        for FIXTURE in FIXTURES:
            meta = self.os.glance_client.add_image(FIXTURE, None)
            self.images[meta['id']] = meta

    def tearDown(self):
        for (image_id, meta) in self.images.items():
            self.os.glance_client.delete_image(image_id)

    def test_get_image(self):
        """Verify the correct details are returned for an image"""
        for (image_id, expected) in self.images.items():
            url = '/images/%s' % (image_id,)
            response, body = self.os.nova_api.request('GET', url)
            self.assertEqual(response['status'], '200')
            actual = json.loads(body)['image']
            self.assertEqual(expected['id'], actual['id'])
