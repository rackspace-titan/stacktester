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

import exceptions
import time
import urlparse
import urllib
import httplib2
try:
    import json
except ImportError:
    import simplejson as json


from domainobjects import client
from domainobjects import flavors
from domainobjects import images
from domainobjects import servers
import glance.client
import utils


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

    def __init__(self, api_user=None, api_key=None, api_url=None):
        api_user = api_user or utils.get_api_user()
        api_key = api_key or utils.get_api_key()
        api_url = api_url or utils.get_api_url()

        self.client = client.OpenStackClient(api_user, api_key, api_url)

        glance_host = utils.get_glance_host()
        glance_port = utils.get_glance_port()
        self.glance_client = glance.client.Client(glance_host, glance_port)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`novaclient.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
