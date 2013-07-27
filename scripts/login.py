# Copyright (c) Jakky89 2013.
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
Default set of commands bundled with cuwo
"""

from cuwo.script import ServerScript, command, admin
from cuwo.vector import Vector3
from cuwo.common import get_chunk
from twisted.internet import reactor

import platform
import sys
import cuwo.database


class LoginServer(ServerScript):
    pass

def get_class():
    return LoginServer


LOGIN_HELP = [
    'When you already have an ID please use /login <ID> <password>.',
    'Use /register <password> to register in order to get an ID.',
    'Please remember these login data because it is needed to',
    'assign the game data.'
]

def on_new_connection(self, connection):
    reactor.callLater(20, connection.send_lines, LOGIN_HELP)


@command
def register(script, password):
    if not password:
        return '[INFO] Register with password to get your login id for future logins: /register <password>'
    reg_id = database.register_player(script.server.db_con, script.connection.name, password)
    if reg_id:
        return '[REGISTRATION] Please note that you have to do /login %s %s now to log in.' % (reg_id, password)
    return '[ERROR] Could not register!'


@command
def login(script, id, password):
    if not id or not password:
        return '[INFO] Command to login with your ID and password: /login <ID> <password>'
    login_res = database.login_player(script.server.db_con, script.connection.name, id, password)
    if not login_res:
        return '[LOGIN] Login failed!'
    else:
        return '[LOGIN] Successfully logged in!' % id
    return '[ERROR] Invalid password!'
