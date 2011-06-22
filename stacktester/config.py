import ConfigParser


CONFIG = None

def _get_default_config():
    return {
        'nova': {
            'host': "127.0.0.1",
            'port': 8774,
            'user': "admin",
            'base_url': "v1.1/",
            'api_key': "",
        },
        'glance': {
            'host': "127.0.0.1",
            'port': 9292
        },
    }

def load_config(path):
    defaults = _get_default_config()
    config = ConfigParser.SafeConfigParser(defaults=defaults)
    config.read(path)
    return config
