
import common.http
import json
import subprocess

class API(common.http.Client):
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

    def wait_for_server_status(self, serverid, status='ACTIVE', timeout=180):

        def check_response(resp, body):
            data = json.loads(body)
            return data['server']['status'] == status

        self.poll_request(
            'GET', 
            '/servers/%s' % serverid, 
            check_response, 
            timeout=timeout)

    def wait_for_response_status(self, serverid, status=200, timeout=180):

        def check_response(resp, body):
            return resp['status'] == str(status)

        self.poll_request(
            'GET', 
            '/servers/%s' % serverid, 
            check_response, 
            timeout=timeout)

    def request(self, method, url, **kwargs):
        headers = kwargs.get('headers', {})
        headers['X-Auth-Token'] = self._authenticate(self.user, self.apikey)
        kwargs['headers'] = headers
        return super(API, self).request(method, url, **kwargs)

    def _add_flavor(self, flavor):
        #TODO: Get connection info from config
        subprocess.call(["ssh", "root@nova1", "nova-manage instance_type create", 
                        str(flavor["name"]),
                        str(flavor["ram"]),
                        str(flavor["vcpus"]),
                        str(flavor["disk"]),
                        str(flavor["flavorid"]),
        ]) 

    def _delete_flavor(self, flavor_name):
        #TODO: Get connection info from config
        subprocess.call(["ssh", "root@nova1", "nova-manage instance_type delete ",
                    flavor_name,
                    "--purge",
            ]) 
