
import common.http

class API(common.http.Server):
    def __init__(self, host, port, base_url, user, apikey):
        super(API, self).__init__(host, port, base_url)
        self.user = user
        self.apikey = apikey

    def _authenticate(self, user, api_key):
        headers = {'X-Auth-User': user, 'X-Auth-Key': api_key}
        resp, body = super(API, self).request('GET', '', headers=headers)
        try:
            return resp['x-auth-token']
        except KeyError:
            print "Failed to authenticate user"
            raise

        #TODO: use management_url

    def request(self, method, url, **kwargs):
        headers = kwargs.get('headers', {})
        headers['X-Auth-Token'] = self._authenticate(self.user, self.apikey)
        kwargs['headers'] = headers
        return super(API, self).request(method, url, **kwargs)
