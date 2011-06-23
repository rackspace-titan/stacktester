import glance.client

import stacktester.config
import stacktester.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        config = stacktester.config.StackConfig()
        self.nova = self._load_nova(config)
        self.glance = self._load_glance(config)

    def _load_nova(self, config):
        host = config.nova.host
        port = config.nova.port
        base_url = config.nova.base_url
        user = config.nova.username
        api_key = config.nova.api_key
        return stacktester.nova.API(host, port, base_url, user, api_key)

    def _load_glance(self, config):
        host = config.glance.host
        port = config.glance.port
        return glance.client.Client(host, port)
