import ConfigParser


class NovaConfig(object):
    """Provides configuration information for connecting to Nova."""

    def __init__(self, conf):
        """Initialize a Nova-specific configuration object."""
        self.conf = conf

    def get(self, item_name, default_value):
        try:
            return self.conf.get("nova", item_name)
        except ConfigParser.NoSectionError:
            return default_value

    @property
    def host(self):
        """Host for the Nova HTTP API. Defaults to 127.0.0.1."""
        return self.get("host", "127.0.0.1")

    @property
    def port(self):
        """Port for the Nova HTTP API. Defaults to 8774."""
        return int(self.get("port", 8774))

    @property
    def username(self):
        """Username to use for Nova API requests. Defaults to 'admin'."""
        return self.get("user", "admin")

    @property
    def base_url(self):
        """Base of the HTTP API URL. Defaults to '/v1.1'."""
        return self.get("base_url", "/v1.1")

    @property
    def api_key(self):
        """API key to use when authenticating. Defaults to 'admin_key'."""
        return self.get("api_key", "admin_key")


class GlanceConfig(object):
    """Provides configuration information for connecting to Glance."""

    def __init__(self, conf):
        """Initialize a Glance-specific configuration object."""
        self.conf = conf

    def get(self, item_name, default_value):
        try:
            return self.conf.get("glance", item_name)
        except ConfigParser.NoSectionError:
            return default_value

    @property
    def host(self):
        """Host for the Glance HTTP API. Defaults to '127.0.0.1'."""
        return self.get("host", "127.0.0.1")

    @property
    def port(self):
        """Port for the Glance HTTP API. Defaults to 9292."""
        return int(self.get("port", 9292))


class StackConfig(object):
    """Provides `stacktester` configuration information."""

    _path = None

    def __init__(self, path=None):
        """Initialize a configuration from a path."""
        self._path = path or self._path
        self._conf = self.load_config(self._path)
        self.glance = GlanceConfig(self._conf)
        self.nova = NovaConfig(self._conf)

    def load_config(self, path=None):
        """Read configuration from given path and return a config object."""
        config = ConfigParser.SafeConfigParser()
        config.read(path)
        return config
