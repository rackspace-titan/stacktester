
from stacktester import nova
import glance.client


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        self.nova_api = nova.API('localhost', 8774, 'v1.1/',
                                 'admin', 'd9DBcehAEiPAEoAZAb1e')
        self.glance_client = glance.client.Client('localhost', 9292)
