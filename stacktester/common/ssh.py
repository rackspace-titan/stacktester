import time
import socket 
import warnings

from stacktester import exceptions

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


class Client(object):


    def __init__(self, host, username, password, timeout=300):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout

    def _ssh_connection(self):
        """Returns an ssh connection to the specified host"""
        _timeout = True
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        _start_time = time.time()

        while (time.time() - self.timeout) < _start_time:
            try:
                ssh.connect(self.host, username=self.username, 
                    password=self.password, look_for_keys=False,
                    timeout=self.timeout)
                _timeout = False
                break
            except socket.error:
                continue
        if _timeout:
            raise socket.error("SSH connect timed out")
        return ssh

    def connect_until_closed(self):
        """Connect to the server and wait until connection is lost"""
        try:
            ssh = self._ssh_connection()
            _transport = ssh.get_transport()
            _start_time = time.time()
            while _transport.is_active() and\
                ((time.time() - self.timeout) < _start_time):
                time.sleep(5)
            ssh.close()
        except EOFError:
            return
        except paramiko.AuthenticationException:
            return
        except socket.error:
            return

    def exec_command(self, cmd):
        """Execute the specified command on the server.

        :returns: stdin, stdout, stderr

        """

        ssh = self._ssh_connection()
        stdin, stdout, stderr = ssh.exec_command(cmd)
        ssh.close()
        return stdin, stdout, stderr

    def get_time_started(self):
        """Return the time the server was started"""
        ssh = self._ssh_connection()
        stdin, stdout, stderr = ssh.exec_command("cat /proc/uptime")
        uptime = float(stdout.read().split().pop(0))
        ssh.close()
        return time.time() - uptime
