import json
import logging
import subprocess

import paramiko

import stacktester.common.http


class API(stacktester.common.http.Client):
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

        #TODO: use management_url

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
    
    #TODO Consider genericizing so servers/images share common code
    def wait_for_image_status(self, image_id, status='ACTIVE', **kwargs):
        """Wait for the image status to be equal to the status passed in.

        :param image_id: Image ID to query.
        :param status: The status string to look for.
        :returns: None

        """
        def check_response(resp, body):
            data = json.loads(body)
            return data['image']['status'] == status

        self.poll_request(
            'GET',
            '/images/%s' % image_id,
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


class AdminClient(object):
    """Administrative client for remotely managing Nova installations."""

    def __init__(self, host, ssh_port, ssh_username):
        """Initialize an admin client.

        :param host: The hostname/IP of a Nova node with nova-manage installed.
        :param ssh_port: The ssh port of a Nova node with nova-manage installed.
        :param ssh_username: The username to use via SSH to execute commands.
        :returns: None

        """
        self.host = host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self._ssh = self._connect()

    def _connect(self):
        """Setup the SSH client to connect to the target server."""
        self._set_paramiko_logging()
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(self.host, port=self.ssh_port,
                       username=self.ssh_username)
        return client

    def _set_paramiko_logging(self):
        """Move from DEBUG -> WARN level logging on paramiko."""
        logger = logging.getLogger("paramiko.transport")
        logger.setLevel(logging.WARN)

    def _remote_call(self, command):
        """Perform a command on the remote node.

        :param command: The command to perform, including all options/flags.
        :returns: True if exit code == 0, False if exit code != 0

        """
        session = self._ssh.get_transport().open_session()
        stdin, stdout, stderr = session.exec_command(command)
        exit_code = session.recv_exit_status()
        success = exit_code == 0

        if not success:
            print "%(command)s returned %(exit_code)d" % locals()
            print "Standard Out: %(stdout)s" % locals()
            print "Standard Error: %(stderr)s" % locals()

        return success

    def add_flavor(self, flavor):
        """Add a flavor, using the 'nova-manage' command via SSH.

        :param flavor: Dictionary describing a flavor to add to Nova's DB.
        :returns: None

        """
        self._ssh.exec_command("nova-manage instance_type create %(name)s "
                               "%(ram)s %(vcpus)s %(disk)s %(flavorid)s" %
                               flavor)

    def delete_flavor(self, flavor_name):
        """Delete a flavor, using the 'nova-manage' command via SSH.

        :param flavor_name: The name of the flavor to delete.
        :returns: None

        """
        self._ssh.exec_command("nova-manage instance_type delete "
                               "%(flavor_name)s --purge" % locals())
