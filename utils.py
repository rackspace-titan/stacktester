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

import os
import unittest


def fail(msg):
    raise AssertionError(msg)


def _get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        print "Failed to retrieve %s" % name


def get_api_user():
    return _get_env_variable("NOVA_USERNAME")


def get_api_key():
    return _get_env_variable("NOVA_API_KEY")


def get_api_url():
    return _get_env_variable("NOVA_URL")


class TestCase(unittest.TestCase):
    def assertIsInstance(self, obj, cls):
        assert isinstance(obj, cls), "Object is not of instance %s" % (cls,)
