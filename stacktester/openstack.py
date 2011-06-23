import glance.client

import stacktester.config
import stacktester.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        config = stacktester.config.StackConfig()
        self.nova = self._load_nova(config)
        self.nova_admin = self._load_nova_admin(config)
        self.glance = self._load_glance(config)

    def _load_nova(self, config):
        return stacktester.nova.API(config.nova.host,
                                    config.nova.port,
                                    config.nova.base_url,
                                    config.nova.username,
                                    config.nova.api_key)

    def _load_nova_admin(self, config):
        return stacktester.nova.AdminClient(config.nova.host,
                                            config.nova.ssh_username)

    def _load_glance(self, config):
        return glance.client.Client(config.glance.host, config.glance.port)
