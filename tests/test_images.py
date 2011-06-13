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

from domainobjects.utils import *
from nose.tools import assert_equal
from domainobjects.openstack import OpenStack
from domainobjects.images import Image

class TestImages:
    
    @classmethod   
    def setup_class(self):
        self.os = OpenStack(get_username(), get_api_key())
        self.server = self.os.servers.create(name="testserver", 
                                image="http://glance1:9292/v1/images/3",
                                flavor="http://172.19.0.3:8774/v1.1/flavors/3")
        self.server.waitForStatus('ACTIVE')
    
    @classmethod
    def teardown_class(self):
    	self.server.delete()

    def test_get_image_details(self):
        """        
        Verify the correct details are returned for an image
        """
        
        image = self.os.images.get(1)
        assert_isinstance(image, Image)
        assert_equal(image.id, 1)
        assert_equal(image.name, 'ari-tty')

    def test_create_delete_image(self):
        """
        Verify that a new image can be created and deleted
        """
        
        image = self.os.images.create("Just in case",
                                "http://172.19.0.3:8774/v1.1/servers/%s" % 
                                str(self.server.id))
        assert_isinstance(image, Image)
        self.os.images.delete(iimage.id)

