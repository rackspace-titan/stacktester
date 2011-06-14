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
from domainobjects import servers
import utils


class ServerMetaTest(utils.TestCase):

    def setUp(self):
        self.os = openstack.OpenStack()
        self.server = self.os.servers.create(name="testserver",
                                image="http://glance1:9292/v1/images/3",
                                flavor="http://172.19.0.3:8774/v1.1/flavors/3",
                                meta={'testKey': 'testData'})
        self.server.waitForStatus('ACTIVE')

    def tearDown(self):
	    self.server.delete()

    def test_get_servers_metdata(self):
        """
        Test that we can retrieve metadata for a server.
        """

        # Get a pristine server object
        s = self.os.servers.get(self.server)

        # Verify that it has the value we expect
        self.assertEqual(s.metadata['testKey'], 'testData')

    def test_create_delete_metadata(self):
        pass

    def test_update_metadata(self):
        pass

