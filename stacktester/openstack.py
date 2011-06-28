import glance.client

import stacktester.config
import stacktester.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        self.config = stacktester.config.StackConfig()
        self.nova = self._load_nova()

    def _load_nova(self):
        return stacktester.nova.API(self.config.nova.host,
                                    self.config.nova.port,
                                    self.config.nova.base_url,
                                    self.config.nova.username,
                                    self.config.nova.api_key)
