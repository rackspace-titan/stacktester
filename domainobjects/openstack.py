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

"""
novaclient module.
"""

__version__ = '2.4'

from client import OpenStackClient
from exceptions import (OpenStackException, BadRequest,
        Unauthorized, Forbidden, NotFound, OverLimit)
from flavors import FlavorManager, Flavor
from images import ImageManager, Image
from servers import (ServerManager, Server, REBOOT_HARD,
                                 REBOOT_SOFT)

class OpenStack(object):
    """
    Top-level object to access the OpenStack Nova API.

    Create an instance with your creds::

        >>> os = OpenStack(USERNAME, API_KEY, AUTH_URL)

    Then call methods on its managers::

        >>> os.servers.list()
        ...
        >>> os.flavors.list()
        ...

    &c.
    """

    def __init__(self, username, apikey,
                 auth_url='http://172.19.0.3:8774/v1.1/'):
        self.client = OpenStackClient(username, apikey, auth_url)
        self.flavors = FlavorManager(self)
        self.images = ImageManager(self)
        self.servers = ServerManager(self)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`novaclient.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
