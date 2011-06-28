import stacktester.config
import stacktester.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        config = stacktester.config.StackConfig()
        self.nova = stacktester.nova.API(config.nova.host,
                                         config.nova.port,
                                         config.nova.base_url,
                                         config.nova.username,
                                         config.nova.api_key)
