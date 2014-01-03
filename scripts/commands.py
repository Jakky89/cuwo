# Copyright (c) Mathias Kaerlev, Somer Hayter, sarcengm and Jakky89 2013.
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
from cuwo.common import get_chunk
from cuwo.constants import CLASS_NAMES, CLASS_SPECIALIZATIONS
from cuwo.packet import HitPacket, HIT_NORMAL
from cuwo.vector import Vector3
from twisted.internet import reactor
from cuwo import database
from cuwo import common

import platform
import sys


class CommandServer(ServerScript):
    pass


def get_class():
    return CommandServer


@command
@admin
def say(script, *message):
    """Sends a global server message."""
    message = ' '.join(message)
    script.server.send_chat(message)


@command
def server(script):
    """Returns information about the server's platform."""
    msg = 'Server is running on %r' % platform.system()
    revision = script.server.git_rev
    if revision is not None:
        msg += ', revision %s' % revision
    return msg


@command
def register(script, password=None, repeating=None):
    if not password or not repeating:
        return '[INFO] Use /register <Password> <Password Repeating> to register in order to get your own unique numeric ID.'
    if password != repeating:
        return '[REGISTRATION] Your password does not equal its repeating.'
    regid = database.register_player(script.server.db_con, script.connection.name, script.connection.address.host, password)
    if regid:
        database.update_player(script.server.db_con, regid, script.connection.name)
        return '[REGISTRATION] You can use /login %s %s now everytime you want to login.' % (regid, password)
    return '[ERROR] Registration failed.'


@command
def login(script, id, password):
    if not id or not password:
        return '[INFO] Use /login <ID> <Password> when you are already registered else use /register <Password> <Password Repeating> to register in order to get your own unique numeric ID.'
    try:
        id = int(id)
    except Exception:
        return '[ERROR] Invalid ID given.'
    dbres = database.login_player(script.server.db_con, script.connection.name, id, password)
    if dbres:
        script.connection.login_id = id
        database.update_player(script.server.db_con, id, script.connection.name)
        if not dbres.rank is None:
            script.connection.rights.update(dbres.rank)
            return '[LOGIN] Successfully logged in as %s %s. Your last login name was %s with IP %s.' % (dbres.rank.upper(), script.connection.name, dbres.ingame_name, dbres.last_ip)
        return '[LOGIN] Successfully logged in as %s. Your last login name was %s with IP %s.' % (script.connection.name, dbres.ingame_name, dbres.last_ip)
    else:
        return '[ERROR] To many arguments!'
    return '[ERROR] Login failed.'


@command
def help(script, name=None):
    """Returns information about commands."""
    if name is None:
        commands = [item.name for item in script.get_commands()]
        commands.sort()
        return 'Commands: ' + ', '.join(commands)
    else:
        command = script.get_command(name)
        if command is None:
            return 'No such command'
        return command.get_help()


@command
@admin
def kick(script, name):
    """Kicks the specified player."""
    try:
        player = script.get_player(name)
        if player:
            player.kick('Kicked by Admin')
            return '[SUCCESS] Kicked %s' % name
    except:
        return '[ERROR] Player %s could not be kicked!' % name



@command
@admin
def setrank(script, name, rank):
    if not name or not rank:
        return '[INFO] Use /setrank <Name> <Rank> to set the rank of user with the given name.'
    player = script.get_player(name)
    if not player:
        return '[ERROR] Player %s not found.' % name
    if not player.login_id:
        return '[ERROR] Player %s is not logged in!' % name
    if not (rank in script.server.ranks):
        script.connection.send_chat('[WARNING] Unknown rank: %s' % rank)
    ret = database.set_player_rank(script.server.db_con, player.login_id, rank)
    if ret is True:
        script.connection.rights.update(rank)
        player.send_chat('[INFO] You are now %s' % rank.upper())
        return '[SUCCESS] Rank of %s set to %s' % (name, rank)
    return '[RANK] Could not set rank!'


@command
@admin
def setclock(script, value):
    """Sets the time of day. Format: hh:mm."""
    try:
        script.server.set_clock(value)
        return '[SUCCESS] Time set to %s' % value
    except ValueError:
        return '[EXCEPTION] Invalid value!'
    return '[ERROR] Time could not be set!'


@command
@admin
def spawnmob(script, value):
    try:
        entity = script.server.create_entity_data(value)
    except ValueError:
        return '[ERROR] Invalid value!'
    except:
        pass
    if script.connection.position:
        entity.position(script.connection.position.copy())
    return '[ERROR] Could not spawn mob!'


@command
@admin
def heal(script, name=None, heal_amount=None):
    player = script.get_player(name)
    player.heal(amount, '[INFO] You have been healed by admin')
    return 'Healed %s' % player.name


@command
@admin
def restart(script, delay=10, *args):
    try:
        delay = int(delay)
    except Exception:
        return
    reason = None
    if len(args) > 0:
        reason = ' '.join(args)
    # Todo: add scheduler function
    # reactor.callLater(10, 'restart', delay)



@command
@admin
def kill(script, name=None):
    """Kills a player."""
    player = script.get_player(name)
    player.kill(script.connection)
    return None


@command
@admin
def stun(script, name, milliseconds=1000):
    """Stuns a player for a specified duration of time."""
    player = script.get_player(name)
    damage_player(script, player, stun_duration=int(milliseconds))
    message = '%s was stunned' % player.name
    print message
    script.server.send_chat(message)


@command
@admin
def heal(script, name=None, hp=1000):
    """Heals a player by a specified amount."""
    player = script.get_player(name)
    damage_player(script, player, damage=-int(hp))
    message = '%s was healed' % player.name
    return message


@command
@admin
def stop(script, delay=10):
    try:
        delay = int(delay)
    except Exception:
        return
    reactor.callLater(delay, script.server.stop)
    script.server.send_chat('The server will shut down in %s seconds.' % delay)


@command
def spawn(script):
    player = script.get_player(name)
    if player.teleport(0, 0, 0):
        return '[INFO] Teleported to spawn.'
    return '[ERROR] Could not teleport to spawn.'


@command
def help(script):
    return script.server.config.base.help


@command
def list(script):
    plcount = len(script.server.connections)
    if plcount <= 0:
        return '[INFO] There are currently no players online.'
    plrs = []
    for player in script.server.players.values():
        plrs.append('%s (%s)' % (player.name, common.get_entity_type_level_str(player.entity_data)))
    return '[INFO] %s/%s players online: %s' % (plcount, config.max_players, ', '.join(plrs))


@command
def player(script, name):
    """Returns information about a player."""
    player = script.get_player(name)
    entity = player.entity_data
    typ = entity.class_type
    klass = CLASS_NAMES[typ]
    spec = CLASS_SPECIALIZATIONS[typ][entity.specialization]
    level = entity.level
    return "'%s' is a lvl %s %s (%s)" % (player.name, level, klass, spec)


@command
def tell(script, name=None, *args):
    """Sends a private message to a player."""
    if not name:
        return '[INFO] Command to tell something to a specific player: /tell <player> <message>'
    try:
        player = script.get_player(name)
        if not player:
            return '[ERROR] Could not find player with that name!'
        if player is script.connection:
            return '[ERROR] You can not tell messages back to yourself!'
        message = '%s -> %s: %s' % (script.connection.name, player.name, ' '.join(args))
        player.send_chat(message)
        return message
    except:
        pass
    return '[EXCEPTION] Could not tell message to %s!' % player.name


@command
def whereis(script, name=None):
    """Shows where a player is in the world."""
    player = script.get_player(name)
    if player is script.connection:
        message = 'You are at %s'
    else:
        message = '%s is at %%s' % player.name
    return message % (get_chunk(player.position),)


@command
def player(script, name):
    """Returns information about a player."""
    player = script.get_player(name)
    entity = player.entity_data
    typ = entity.class_type
    klass = CLASS_NAMES[typ]
    spec = CLASS_SPECIALIZATIONS[typ][entity.specialization]
    level = entity.level
    return "'%s' is a lvl %s %s (%s)" % (player.name, level, klass, spec)


@command
def scripts(script):
    """Lists the currently loaded scripts."""
    return 'Scripts: ' + ', '.join(script.server.scripts.items)
