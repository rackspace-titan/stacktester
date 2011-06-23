
import stacktester
from stacktester import nova
import glance.client


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self, config=None):
        if config is None:
            config = stacktester.CONFIG
        self.nova_api = self._load_nova_api(config)
        self.glance_client = self._load_glance_client(config)

    def _load_nova_api(self, config):
        host = config.get('nova', 'host')
        port = config.getint('nova', 'port')
        base_url = config.get('nova', 'base_url')
        user = config.get('nova', 'user')
        api_key = config.get('nova', 'api_key')
        return nova.API(host, port, base_url, user, api_key)

    def _load_glance_client(self, config):
        host = config.get('nova', 'host')
        port = config.getint('nova', 'port')
        return glance.client.Client(host, port)
