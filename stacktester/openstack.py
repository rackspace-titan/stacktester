import time
import socket 
import warnings

import stacktester.config
import stacktester.nova

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        self.config = stacktester.config.StackConfig()
        self.nova = stacktester.nova.API(self.config.nova.host,
                                    self.config.nova.port,
                                    self.config.nova.base_url,
                                    self.config.nova.username,
                                    self.config.nova.api_key)

    def get_ssh_connection(self, host, username, password):
        """Returns an ssh connection to the specified host"""
        ssh_timeout = self.config.nova.ssh_timeout
        _timeout = True
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        _start_time = time.time()

        while (time.time() - ssh_timeout) < _start_time:
            try:
                ssh.connect(host, username=username, 
                    password=password, look_for_keys=False,
                    timeout=ssh_timeout)
                _timeout = False
                break
            except socket.error:
                continue
        if _timeout:
            raise socket.error("SSH connect timed out")
        return ssh
