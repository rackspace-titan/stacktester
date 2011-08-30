import stacktester.config
import stacktester.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        self.config = stacktester.config.StackConfig()
        self.nova = stacktester.nova.API(self.config.nova.host,
                                    self.config.nova.port,
                                    self.config.nova.auth_base_path,
                                    self.config.nova.username,
                                    self.config.nova.api_key,
                                    self.config.nova.project_id,
                                    self.config.nova.service_name)
