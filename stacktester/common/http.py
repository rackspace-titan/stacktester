
import httplib2
import os


class Client(object):

    USER_AGENT = 'python-nova_test_client'

    def __init__(self, host='localhost', port=80, base_url=''):
        #TODO: join these more robustly
        self.base_url = "http://%s:%s/%s" % (host, port, base_url)

    def request(self, method, url, **kwargs):
        self.http_obj = httplib2.Http()

        params = {}
        params['headers'] = {'User-Agent': self.USER_AGENT}
        params['headers'].update(kwargs.get('headers', {}))

        if 'body' in kwargs:
            params['body'] = kwargs.get('body')

        req_url = "%s/%s" % (self.base_url, url)
        resp, body = self.http_obj.request(req_url, method, **params)
        return resp, body
