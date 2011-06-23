
import httplib2
import os
import time


class Client(object):

    USER_AGENT = 'python-nova_test_client'

    def __init__(self, host='localhost', port=80, base_url=''):
        #TODO: join these more robustly
        self.base_url = "http://%s:%s/%s" % (host, port, base_url)

    def poll_request(self, method, url, check_response, **kwargs):

        timeout = kwargs.pop('timeout', 180)
        # Start timestamp
        start_ts = int(time.time())

        resp, body = self.request(method, url, **kwargs)
        while ( (int(time.time()) - start_ts < (timeout * 1000) 
                 and not check_response(resp, body))):
            time.sleep(2)
            resp, body = self.request(method, url, **kwargs)

        #TODO we can probably make this better so we don't have
        # to run check_response again, but I want this func to
        # return True/False so we know if it timed out or actually
        # got the response we wanted
        return check_response(resp, body)
        

    def request(self, method, url, **kwargs):
        self.http_obj = httplib2.Http()

        params = {}
        params['headers'] = {'User-Agent': self.USER_AGENT}
        params['headers'].update(kwargs.get('headers', {}))
        if 'Content-Type' not in kwargs.get('headers',{}):
            params['headers']['Content-Type'] = 'application/json'

        if 'body' in kwargs:
            params['body'] = kwargs.get('body')

        req_url = "%s/%s" % (self.base_url, url)
        resp, body = self.http_obj.request(req_url, method, **params)
        return resp, body
