
from stacktester import openstack

import json
import unittest2 as unittest


class ImagesTest(unittest.TestCase):

    def setUp(self):
        self.os = openstack.Manager()
        self.images = {}
        
        resp, body = self.os.nova.request(
            'GET', '/images/%s' % self.os.config.env.get('image_ref'))
        data = json.loads(body)
        self.images[str(data['id'])] = data

    def tearDown(self):
        pass

    def _assert_image_basic(self, image, expected):
        self.assertEqual(expected['id'], image['id'])
        self.assertEqual(expected['name'], image['name'])

        #TODO: check links

    def _assert_image_metadata(self, image, expected):
        expected_meta = expected['properties']
        self.assertTrue('metadata' in image)
        image_meta = image['metadata']
        self.assertEqual(len(expected_meta), len(image_meta))
        for (key, value) in expected_meta.items():
            self.assertTrue(key in image_meta)
            self.assertEqual(expected_meta[key], image_meta[key])

    def _assert_image_detailed(self, image, expected):
        self._assert_image_basic(image, expected)

        self.assertEqual(expected['name'], image['name'])
        self.assertEqual('QUEUED', image['status'])

        #TODO: make this more robust
        created_at = expected['created_at'].split('.')[0]+'Z'
        self.assertEqual(created_at, image['created'])
        self.assertEqual(expected['updated_at'], image['updated'])

        self._assert_image_metadata(image, expected)

    def test_get_images(self):
        """Verify the correct list of image entities is returned"""
        response, body = self.os.nova.request('GET', '/images')

        self.assertEqual(response['status'], '200')
        result = json.loads(body)['images']

        # expect to only see public images
        self.assertEqual(len(result), 1)

        for image in result:
            expected = self.images[str(image['id'])]
            self._assert_image_basic(image, expected)

    def test_get_images_detailed(self):
        """Verify the correct list of detailed image entities is returned"""
        response, body = self.os.nova.request('GET', '/images/detail')

        self.assertEqual(response['status'], '200')
        result = json.loads(body)['images']

        # expect to only see public images
        self.assertEqual(len(result), 1)

        for image in result:
            expected = self.images[str(image['id'])]
            self._assert_image_detailed(image, expected)

    def test_get_image(self):
        """Verify the correct entities are returned for each image"""
        for (image_id, expected) in self.images.items():
            url = '/images/%s' % (image_id,)
            response, body = self.os.nova.request('GET', url)

            self.assertEqual(response['status'], '200')
            result = json.loads(body)['image']
            self._assert_image_detailed(result, expected)

    def test_get_image_metadata(self):
        """Verify correct list of metadata entities are returned per image"""
        for (image_id, expected) in self.images.items():
            url = '/images/%s/meta' % (image_id,)
            response, body = self.os.nova.request('GET', url)

            self.assertEqual(response['status'], '200')
            result = json.loads(body)
            self._assert_image_metadata(result, expected)

    def test_get_image_metadata_item(self):
        """Verify the correct metadata entities are returned for each image"""
        for (image_id, expected) in self.images.items():
            for (meta_key, meta_value) in expected['properties'].items():
                url = '/images/%s/meta/%s' % (image_id, meta_key)
                response, body = self.os.nova.request('GET', url)

                self.assertEqual(response['status'], '200')
                result = json.loads(body)
                self.assertEqual(result, {'meta': {meta_key: meta_value}})

    def test_create_delete_server_image(self):
        """Verify an image can be created from an existing server"""
        post_body = json.dumps({
            'server' : {
                'name' : 'testserver',
                'imageRef' : self.os.config.env.get('image_ref'),
                'flavorRef' : self.os.config.env.get('flavor_ref') 
            }
        })

        response, body = self.os.nova.request(
            'POST', '/servers', body=post_body)
        data = json.loads(body)
        server_id = data['server']['id']
        self.os.nova.wait_for_server_status(server_id, 'ACTIVE')

        post_body = json.dumps({
            'image' : {
                'name' : 'backup',
                'serverRef' : str(server_id)               
            }
        })
        response, body = self.os.nova.request(
            'POST', '/images', body=post_body)

        # KNOWN-ISSUE incorrect response code
        #self.assertEqual(response['status'], '202')
        data = json.loads(body)
        image_id = data['image']['id']
        self.os.nova.wait_for_image_status(image_id, 'ACTIVE')

        response, body = self.os.nova.request('DELETE', '/images/%s' % image_id)
        self.assertEqual(response['status'], '204')
        self.os.nova.request('DELETE', '/servers/%s' % server_id)

