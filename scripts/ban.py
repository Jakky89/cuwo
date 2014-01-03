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
Ban management
"""

from cuwo.script import ServerScript, command, admin
from twisted.internet import reactor
from cuwo import database


SELF_BANNED = 'You are banned from this server!'
PLAYER_BANNED = '{name} has been banned: {reason}'
DEFAULT_REASON = 'No reason specified'



class BanServer(ServerScript):

    def ban(self, player_name, ip_address, ban_reason=None):
        database.ban_ip(self.server.db_con, ip_address, script.entity_data.name, reactor.seconds()+86400, ban_reason)
        for connection in self.server.connections.copy():
            if connection.address.host != ip_address:
                continue
            connection.kick(SELF_BANNED)
        message = PLAYER_BANNED.format(name = player_name, reason = ban_reason)
        print message
        self.server.send_chat(message)
        return True

    def unban(self, ip):
        database.unban_ip(self.server.db_con, ip_address)
        return True

    def on_connection_attempt(self, event):
        if database.is_banned_ip(self.server.db_con, event.address.host):
            return SELF_BANNED
        return


def get_class():
    return BanServer


@command
@admin
def ban(script, name, *reason):
    """Bans a player."""
    player = script.get_player(name)
    reason = ' '.join(reason) or DEFAULT_REASON
    script.parent.ban(player.address.host, reason)


@command
@admin
def unban(script, ip):
    """Unbans a player by IP."""
    if script.parent.unban(ip):
        return 'IP "%s" unbanned' % ip
    else:
        return 'IP not found'
