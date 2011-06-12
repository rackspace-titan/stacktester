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

from nose.tools import assert_equal, assert_equal, assert_raises
from domainobjects.openstack import OpenStack
from domainobjects.servers import Server
from domainobjects.utils import *

class TestServers:
    
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

    def test_list_servers(self):
	    serverList = self.os.servers.list()
	    found = False
	    for s in serverList:
	    	if s.name == 'testserver':
	    		found = True
	    assert found

    def test_create_delete_server(self):
        newServer = self.os.servers.create(name="testserver2", 
                                image="http://glance1:9292/v1/images/3",
                                flavor="http://172.19.0.3:8774/v1.1/flavors/3")
        newServer.waitForStatus('ACTIVE')
        createdServer = self.os.servers.get(newServer.id)
        assert_equal('testserver2', createdServer.name)
        assert_equal('202', createdServer.status_code)        
        newServer.delete()
    
    def test_update_server_name(self):
        self.server.update_name(name='modifiedName')
        self.server.waitForStatus('ACTIVE')

        updatedServer = self.os.servers.get(self.server.id)
        assert_equal('modifiedName', updatedServer.name)
        assert_equal('204', updatedServer.status_code)

    def test_create_server_invalid_image(self):
        newServer = self.os.servers.create(name="testserver2", 
                    image="http://glance1:9292/v1/images/9999",
                    flavor="http://172.19.0.3:8774/v1.1/flavors/3")

    def test_create_server_invalid_flavor(self):
        newServer = self.os.servers.create(name="testserver2", 
                    image="http://glance1:9292/v1/images/1",
                    flavor="http://172.19.0.3:8774/v1.1/flavors/99999999")
