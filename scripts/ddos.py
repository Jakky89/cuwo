# Copyright (c) Mathias Kaerlev 2013.
#
# This file is part of cuwo.
#
# cuwo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cuwo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cuwo.  If not, see <http://www.gnu.org/licenses/>.

"""
Prevents Denial of Service attacks to some degree.

XXX should probably be merged with anticheat
"""

from cuwo.script import ServerScript, ConnectionScript
from twisted.internet import reactor


class SaneConnection(ConnectionScript):
    def on_connect(self, event):
        timeout = self.server.config.base.connection_timeout
        self.timeout_call = reactor.callLater(timeout, self.timeout)

    def on_join(self, event):
        self.timeout_call.cancel()

    def timeout(self):
        if self.connection is None:
            return
        host = self.connection.address.host
        print 'Connection %s timed out, disconnecting...' % host
        self.connection.disconnect()


class SaneServer(ServerScript):
    connection_class = SaneConnection

    def on_connection_attempt(self, event):
        host = event.address.host
        max_count = self.server.config.base.max_connections_per_ip
        for connection in self.server.connections:
            if connection.address.host != host:
                continue
            max_count -= 1
            if max_count <= 0:
                break
        else:
            return
        print 'Too many connections from %s, closing...' % host
        return False


def get_class():
    return SaneServer
