import common.http
import json
import subprocess


class API(common.http.Client):
    """Barebones Nova HTTP API client."""

    def __init__(self, host, port, base_url, user, api_key):
        """Initialize Nova HTTP API client.

        :param host: Hostname/IP of the Nova API to test.
        :param port: Port of the Nova API to test.
        :param base_url: Version identifier (normally /v1.0 or /v1.1)
        :param user: The username to use for tests.
        :param api_key: The API key of the user.
        :returns: None

        """
        super(API, self).__init__(host, port, base_url)
        self.user = user
        self.api_key = api_key

    def authenticate(self, user, api_key):
        """Request and return an authentication token from Nova.

        :param user: The username we're authenticating.
        :param api_key: The API key for the user we're authenticating.
        :returns: Authentication token (string)
        :raises: KeyError if authentication fails.

        """
        headers = {'X-Auth-User': user, 'X-Auth-Key': api_key}
        resp, body = super(API, self).request('GET', '', headers=headers)
        try:
            return resp['x-auth-token']
        except KeyError:
            print "Failed to authenticate user"
            raise

        #TODO: use management_url <== what does this mean?

    def wait_for_server_status(self, server_id, status='ACTIVE', **kwargs):
        """Wait for the server status to be equal to the status passed in.

        :param server_id: Server ID to query.
        :param status: The status string to look for.
        :returns: None

        """
        def check_response(resp, body):
            data = json.loads(body)
            return data['server']['status'] == status

        self.poll_request(
            'GET',
            '/servers/%s' % server_id,
            check_response,
            **kwargs)

    def request(self, method, url, **kwargs):
        """Generic HTTP request on the Nova API.

        :param method: Request verb to use (GET, PUT, POST, etc.)
        :param url: The API resource to request.
        :param kwargs: Additional keyword arguments to pass to the request.
        :returns: HTTP response object.

        """
        headers = kwargs.get('headers', {})
        headers['X-Auth-Token'] = self.authenticate(self.user, self.api_key)
        kwargs['headers'] = headers
        return super(API, self).request(method, url, **kwargs)

    def add_flavor(self, flavor):
        """Add a flavor, using the 'nova-manage' command via SSH.

        :param flavor: Dictionary describing a flavor to add to Nova's DB.
        :returns: None

        """
        #TODO: Get connection info from config
        #TODO: Support passwords
        #TODO: Use paramiko
        subprocess.call([
            "ssh",
            "root@nova1",
            "nova-manage instance_type create",
            str(flavor["name"]),
            str(flavor["ram"]),
            str(flavor["vcpus"]),
            str(flavor["disk"]),
            str(flavor["flavorid"]),
        ])

    def delete_flavor(self, flavor_name):
        """Delete a flavor, using the 'nova-manage' command via SSH.

        :param flavor_name: The name of the flavor to delete.
        :returns: None

        """
        #TODO: Get connection info from config
        #TODO: Support passwords
        #TODO: Use paramiko
        subprocess.call([
            "ssh",
            "root@nova1",
            "nova-manage instance_type delete ",
            flavor_name,
            "--purge",
        ])
