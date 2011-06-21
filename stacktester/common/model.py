
class Resource(object):
    """
    A resource represents a particular instance of an object (server, flavor,
    etc). This is pretty much just a bag for attributes.
    """
    def __init__(self, manager, info, resp):
        self.manager = manager
        self._info = info
        self._add_details(info, resp)

    def _add_details(self, info, resp):
        for (k, v) in info.iteritems():
            setattr(self, k, v)
        setattr(self, 'status_code', resp.status)

    def __getattr__(self, k):
        self.get()
        if k not in self.__dict__:
            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys() if k[0] != '_' and
                                                                k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    def get(self):
        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return self._info == other._info

def get_href(obj):
    """
    Abtracts href
    """
    try:
        return obj.href
    except AttributeError:
        return str(obj)

def getid(obj):
    """
    Abstracts the common pattern of allowing both an object or an object's ID
    (integer) as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return int(obj)
