# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Server interface.
"""

import base
import time

REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'


class Server(base.Resource):
    def __repr__(self):
        return "<Server: %s>" % self.name
    
    def waitForStatus(self, status='ACTIVE', timeout=300):

        #Starting timestamp
        start_ts = int(time.time())

    	s = self.manager.get(self.id)
    	while (s.status != status and (int(time.time()) - start_ts) < (timeout * 1000)):
    		time.sleep(2)
    		s = self.manager.get(self.id)

    def delete(self):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self.manager.delete(self)

    def update_name(self, name):
        """
        Update the name or the password for this server.

        :param name: Update the server's name.
        :param password: Update the root password.
        """
        self.manager.update_name(self, name)

    def share_ip(self, ipgroup, address, configure=True):
        """
        Share an IP address from the given IP group onto this server.

        :param ipgroup: The :class:`IPGroup` that the given address belongs to.
        :param address: The IP address to share.
        :param configure: If ``True``, the server will be automatically
                         configured to use this IP. I don't know why you'd
                         want this to be ``False``.
        """
        self.manager.share_ip(self, ipgroup, address, configure)

    def unshare_ip(self, address):
        """
        Stop sharing the given address.

        :param address: The IP address to stop sharing.
        """
        self.manager.unshare_ip(self, address)

    def reboot(self, type=REBOOT_SOFT):
        """
        Reboot the server.

        :param type: either :data:`REBOOT_SOFT` for a software-level reboot,
                     or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self.manager.reboot(self, type)

    def rebuild(self, image):
        """
        Rebuild -- shut down and then re-image -- this server.

        :param image: the :class:`Image` (or its ID) to re-image with.
        """
        self.manager.rebuild(self, image)

    def resize(self, flavor):
        """
        Resize the server's resources.

        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        self.manager.resize(self, flavor)

    def confirm_resize(self):
        """
        Confirm that the resize worked, thus removing the original server.
        """
        self.manager.confirm_resize(self)

    def revert_resize(self):
        """
        Revert a previous resize, switching back to the old server.
        """
        self.manager.revert_resize(self)

    @property
    def public_ip(self):
        """
        Shortcut to get this server's primary public IP address.
        """
        if len(self.addresses['public']) == 0:
            return ""
        return self.addresses['public'][0]

    @property
    def private_ip(self):
        """
        Shortcut to get this server's primary private IP address.
        """
        if len(self.addresses['private']) == 0:
            return ""
        return self.addresses['private'][0]


class ServerManager(base.ManagerWithFind):
    resource_class = Server

    def get(self, server):
        """
        Get a server.

        :param server: ID of the :class:`Server` to get.
        :rtype: :class:`Server`
        """
        return self._get("/servers/%s" % base.getid(server), "server")

    def list(self):
        """
        Get a list of servers.
        :rtype: list of :class:`Server`
        """
        return self._list("/servers", "servers")

    def list_details(self):
        """
        Get a list of servers.
        :rtype: list of :class:`Server`
        """
        return self._list("/servers/detail", "servers")

    def list_metadata(self, meta):
        return self._create("/servers/", "servers")

    def create(self, name, image, flavor, ipgroup=None, meta=None, files=None):
        """
        Create (boot) a new server.

        :param name: Something to name the server.
        :param image: The :class:`Image` to boot with.
        :param flavor: The :class:`Flavor` to boot onto.
        :param ipgroup: An initial :class:`IPGroup` for this server.
        :param meta: A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param files: A dict of files to overrwrite on the server upon boot.
                      Keys are file names (i.e. ``/etc/passwd``) and values
                      are the file contents (either as a string or as a
                      file-like object). A maximum of five entries is allowed,
                      and each file must be 10k or less.
        """
        body = {"server": {
            "name": name,
            "imageRef": base.get_href(image),
            "flavorRef": base.get_href(flavor),
        }}
        if ipgroup:
            body["server"]["sharedIpGroupId"] = base.getid(ipgroup)
        if meta:
            body["server"]["metadata"] = meta

        # Files are a slight bit tricky. They're passed in a "personality"
        # list to the POST. Each item is a dict giving a file name and the
        # base64-encoded contents of the file. We want to allow passing
        # either an open file *or* some contents as files here.
        if files:
            personality = body['server']['personality'] = []
            for filepath, file_or_string in files.items():
                if hasattr(file_or_string, 'read'):
                    data = file_or_string.read()
                else:
                    data = file_or_string
                personality.append({
                    'path': filepath,
                    'contents': data.encode('base64'),
                })
        return self._create("/servers", body, "server")

    def update_name(self, server, name=None):
        """
        Update the name for a server.

        :param server: The :class:`Server` (or its ID) to update.
        :param name: The new server name
        """

        if name is None:
            return
        body = {"server": {}}
        if name:
            body["server"]["name"] = name
        self._update("/servers/%s" % base.getid(server), body)

    def delete(self, server):
        """
        Delete (i.e. shut down and delete the image) this server.
        """
        self._delete("/servers/%s" % base.getid(server))

    def share_ip(self, server, ipgroup, address, configure=True):
        """
        Share an IP address from the given IP group onto a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param ipgroup: The :class:`IPGroup` that the given address belongs to.
        :param address: The IP address to share.
        :param configure: If ``True``, the server will be automatically
                         configured to use this IP. I don't know why you'd
                         want this to be ``False``.
        """
        server = base.getid(server)
        ipgroup = base.getid(ipgroup)
        body = {'shareIp': {'sharedIpGroupId': ipgroup,
                            'configureServer': configure}}
        self._update("/servers/%s/ips/public/%s" % (server, address), body)

    def unshare_ip(self, server, address):
        """
        Stop sharing the given address.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param address: The IP address to stop sharing.
        """
        server = base.getid(server)
        self._delete("/servers/%s/ips/public/%s" % (server, address))

    def reboot(self, server, type=REBOOT_SOFT):
        """
        Reboot a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param type: either :data:`REBOOT_SOFT` for a software-level reboot,
                     or `REBOOT_HARD` for a virtual power cycle hard reboot.
        """
        self._action('reboot', server, {'type': type})
        
    def change_password(self, server, password):
        """
        Change the server's admin password
        """
        
        self._action('changePassword', server, {'adminPass': password})

    def rebuild(self, server, image):
        """
        Rebuild -- shut down and then re-image -- a server.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param image: the :class:`Image` (or its ID) to re-image with.
        """
        self._action('rebuild', server, {'imageRef': base.get_href(image)})

    def resize(self, server, flavor):
        """
        Resize a server's resources.

        :param server: The :class:`Server` (or its ID) to share onto.
        :param flavor: the :class:`Flavor` (or its ID) to resize to.

        Until a resize event is confirmed with :meth:`confirm_resize`, the old
        server will be kept around and you'll be able to roll back to the old
        flavor quickly with :meth:`revert_resize`. All resizes are
        automatically confirmed after 24 hours.
        """
        self._action('resize', server, {'flavorRef': base.get_href(flavor)})


    def confirm_resize(self, server):
        """
        Confirm that the resize worked, thus removing the original server.

        :param server: The :class:`Server` (or its ID) to share onto.
        """
        self._action('confirmResize', server)

    def revert_resize(self, server):
        """
        Revert a previous resize, switching back to the old server.

        :param server: The :class:`Server` (or its ID) to share onto.
        """
        self._action('revertResize', server)

    def _action(self, action, server, info=None):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        self.api.client.post('/servers/%s/action' % base.getid(server),
                             body={action: info})
