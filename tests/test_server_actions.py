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

import random
import time

from domainobjects import base
from domainobjects.utils import *
from domainobjects.openstack import OpenStack

class TestServerActions():

    @classmethod
    def setup_class(self):
        self.os = OpenStack(get_username(), get_api_key())
        self.server = self.os.servers.create(name="testserver",
                                image="http://glance1:9292/v1/images/3",
                                flavor="http://172.19.0.3:8774/v1.1/flavors/1")
        self.server.waitForStatus('ACTIVE')

    @classmethod
    def teardown_class(self):
        self.server.delete()
        
    def test_rebuild_server(self):
        self.server.rebuild("http://glance1:9292/v1/images/4")
        self.server.waitForStatus('ACTIVE')
        rebuilt_server = self.os.servers.get(self.server)
         

    def test_resize_server_confirm(self):
        """
        Verify the flavor of a server can be changed
        """

        #Resize the server and wait for the action to finish
        new_flavor = self.os.flavors.get(2)
        self.server.resize(2)

        #Confirm the resize
        self.server.confirm_resize()

        #Verify that the server's flavor has changed
        modified_server = self.os.servers.get(self.server)
        assertEquals(new_flavor.name, modified_server.flavorId)

    def test_resize_server_revert(self):
        """
        Verify that a re-sized server can be reverted back to its
        original flavor
        """
        
        # Resize the server and wait for it to finish
        new_flavor = self.os.flavors.get(3)
        self.server.resize(3)

        #Not checking state at the moment because this test would hang

        # Revert the resize
        self.server.revert_resize()

        # Check that the was reverted to its original flavor
        modified_server = self.os.servers.get(server)
        assertEquals(new_flavor.name, modified_server.flavorId)

    def test_reboot_server(self):
        """
        Verify that a server can be rebooted
        """

        self.server.reboot()

        #Need to verify state change

    def test_reboot_server_hard(self):
        """
        Verify that a server can be rebooted
        """

        self.os.servers.reboot(self.server, type='HARD')

        #Need to verify state change
