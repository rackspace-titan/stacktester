class Client(httplib2.Http):

    USER_AGENT = 'python-nova_test_client'

    def __init__(self, user, apikey, auth_url):
        super(OpenStackClient, self).__init__()
        self.user = user
        self.apikey = apikey
        self.auth_url = auth_url

        self.management_url = None
        self.auth_token = None

        # httplib2 overrides
        self.force_exception_to_status_code = True

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json.dumps(kwargs['body'])

        httplib2.debuglevel = 1
        if httplib2.debuglevel == 1:
            print "ARGS:", args
        resp, body = super(OpenStackClient, self).request(*args, **kwargs)
        if httplib2.debuglevel == 1:
            print "RESPONSE", resp
            print "BODY", body
        if body:
            try:
                body = json.loads(body)
            except ValueError, e:
                pass
        else:
            body = None

        if resp.status in (400, 401, 403, 404, 413, 500, 501):
            raise exceptions.from_response(resp, body)

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        if not self.management_url:
            self.authenticate()

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault('headers', {})['X-Auth-Token'] = self.auth_token
            resp, body = self.request(self.management_url + url, method,
                                      **kwargs)
            return resp, body
        except exceptions.Unauthorized, ex:
            try:
                self.authenticate()
                resp, body = self.request(self.management_url + url, method,
                                          **kwargs)
                return resp, body
            except exceptions.Unauthorized:
                raise ex

    def get(self, url, **kwargs):
        url = self._munge_get_url(url)
        return self._cs_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def authenticate(self):
        headers = {'X-Auth-User': self.user, 'X-Auth-Key': self.apikey}
        resp, body = self.request(self.auth_url, 'GET', headers=headers)
        self.management_url = resp['x-server-management-url']
        self.auth_token = resp['x-auth-token']

    def _munge_get_url(self, url):
        """
        Munge GET URLs to always return uncached content.

        The OpenStack Nova API caches data *very* agressively and doesn't
        respect cache headers. To avoid stale data, then, we append a little
        bit of nonsense onto GET parameters; this appears to force the data not
        to be cached.
        """
        scheme, netloc, path, query, frag = urlparse.urlsplit(url)
        query = urlparse.parse_qsl(query)
        query.append(('fresh', str(time.time())))
        query = urllib.urlencode(query)
        return urlparse.urlunsplit((scheme, netloc, path, query, frag))


class OpenStackException(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    def __init__(self, code, message=None, details=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details

    def __str__(self):
        return "%s (HTTP %s)" % (self.message, self.code)


class BadRequest(OpenStackException):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    http_status = 400
    message = "Bad request"


class Unauthorized(OpenStackException):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    http_status = 401
    message = "Unauthorized"


class Forbidden(OpenStackException):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(OpenStackException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class OverLimit(OpenStackException):
    """
    HTTP 413 - Over limit: you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


# NotImplemented is a python keyword.
class HTTPNotImplemented(OpenStackException):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in OpenStackException.__subclasses__())
#
# Instead, we have to hardcode it:
_code_map = dict((c.http_status, c) for c in [BadRequest, Unauthorized,
                   Forbidden, NotFound, OverLimit, HTTPNotImplemented])


def from_response(response, body):
    """
    Return an instance of an OpenStackException or subclass
    based on an httplib2 response.

    Usage::

        resp, body = http.request(...)
        if resp.status != 200:
            raise exception_from_response(resp, body)
    """
    cls = _code_map.get(response.status, OpenStackException)
    if body:
        message = "n/a"
        details = "n/a"
        if hasattr(body, 'keys'):
            error = body[body.keys()[0]]
            message = error.get('message', None)
            details = error.get('details', None)
        return cls(code=response.status, message=message, details=details)
    else:
        return cls(code=response.status)
