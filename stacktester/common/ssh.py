import time
import socket 
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


class Client(object):

    def __init__(self, host, username, password, timeout=300):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout

    def _get_ssh_connection(self):
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

    def _is_timed_out(self, timeout, start_time):
        return (time.time() - timeout) > start_time

    def connect_until_closed(self):
        """Connect to the server and wait until connection is lost"""
        try:
            ssh = self._get_ssh_connection()
            _transport = ssh.get_transport()
            _start_time = time.time()
            _timed_out = self._is_timed_out(self.timeout, _start_time):
            while _transport.is_active() and not _timed_out:
                _timed_out = self._is_timed_out(self.timeout, _start_time):
                time.sleep(5)
            ssh.close()
        except (EOFError, paramiko.AuthenticationException, socket.error):
            return

    def exec_command(self, cmd):
        """Execute the specified command on the server.

        :returns: data read from standard output of the command

        """
        ssh = self._get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read()
        ssh.close()
        return output
