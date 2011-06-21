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

from domainobjects import openstack
from domainobjects import images
import utils


FIXTURES = [
    {
        'name': 'Image1',
        'disk_format': 'vdi',
        'container_format': 'ovf',
    },
]


class ImagesTest(utils.TestCase):

    def setUp(self):
        self.os = openstack.OpenStack()
        self.images = {}
        for FIXTURE in FIXTURES:
            meta = self.os.glance_client.add_image(FIXTURE, None)
            self.images[meta['id']] = meta

    def tearDown(self):
        for (image_id, meta) in self.images.items():
            self.os.glance_client.delete_image(image_id)

    def test_get_image_details(self):
        """Verify the correct details are returned for an image"""
        for (image_id, image_meta) in self.images.items():
            image = self.os.images.get(image_id)
            self.assertIsInstance(image, images.Image)
            self.assertEqual(image.id, image_meta['id'])
            self.assertEqual(image.name, image_meta['name'])
