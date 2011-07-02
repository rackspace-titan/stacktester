import time
import socket 
import warnings

from stacktester import exceptions

import httplib2
import os
import time

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


class Client(object):


    def __init__(self, host='localhost', port=80, base_url=''):
        pass

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

    def connect_until_closed(self, host, username, password):
        """Connect to the server and wait until connection is lost"""
        try:
            ssh = self.get_ssh_connection(host, username, password)
            _transport = ssh.get_transport()
            _start_time = time.time()
            while _transport.is_active() and\
                ((time.time() - self.ssh_timeout) < _start_time):
                time.sleep(5)
            ssh.close()
        except EOFError:
            return
        except paramiko.AuthenticationException:
            return
        except socket.error:
            return

    def get_time_started(self, host, username, password):
        """Return the time the server was started"""
        ssh = self.get_ssh_connection(host, username, password)
        stdin, stdout, stderr = ssh.exec_command("cat /proc/uptime")
        uptime = float(stdout.read().split().pop(0))
        ssh.close()
        return time.time() - uptime
