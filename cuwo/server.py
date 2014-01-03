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

from cuwo.twistedreactor import install_reactor
install_reactor()
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from cuwo.packet import (PacketHandler, write_packet, CS_PACKETS,
                         ClientVersion, JoinPacket, SeedData, EntityUpdate,
                         ClientChatMessage, ServerChatMessage,
                         create_entity_data, UpdateFinished, CurrentTime,
                         ServerUpdate, ServerFull, ServerMismatch,
                         INTERACT_DROP, INTERACT_PICKUP, ChunkItemData,
                         ChunkItems, InteractPacket, PickupAction,
                         HitPacket, ShootPacket)
from cuwo.types import IDPool, MultikeyDict, AttributeSet
from cuwo.vector import Vector3
from cuwo import constants
from cuwo.common import (get_clock_string, parse_clock, parse_command,
                         filter_string, get_distance_3d,
                         get_needed_total_xp, get_entity_type_level_str)
from cuwo.script import ScriptManager
from cuwo.config import ConfigObject
from cuwo import database
from cuwo import entity
from cuwo.world import (World, Sector, Chunk, Locatable)

import re
import collections
import imp
import zipimport
import os
import sys
import json
import math
import random
import pprint
import traceback

# initialize packet instances for sending
join_packet = JoinPacket()
seed_packet = SeedData()
chat_packet = ServerChatMessage()
entity_packet = EntityUpdate()
interact_packet = InteractPacket()
update_finished_packet = UpdateFinished()
time_packet = CurrentTime()
mismatch_packet = ServerMismatch()
server_full_packet = ServerFull()


class CubeWorldConnection(Protocol):
    """
    Protocol used for players
    """
    connection_state = 0
    entity_id = None
    entity_data = None
    login_id = None
    change_index = -1
    scripts = None
    chunk = None

    old_name = None
    old_pos = None
    old_health = None
    old_level = None
    old_xp = None

    # used for anti chat spamming
    time_last_chat      = 0
    chat_messages_burst = 0

    # used for detecting dead connections
    time_last_packet = 0
    time_last_rate = 0
    packet_count = 0
    packet_rate = 0
    # used for basic DoS protection
    packet_burst = 0

    def __init__(self, server, addr):
        self.address = addr
        self.server = server

    # connection methods

    def connectionMade(self):
        if self.connection_state != 0:
            self.disconnect('Unexpected data')
            return
        self.connection_state = 1
        server = self.server
        if len(server.connections) >= server.config.base.max_players:
            # For being able to allow joining by external scritps although server is full
            ret = self.scripts.call('on_join_full_server').result
            if ret is not True:
                self.send_packet(server_full_packet)
                self.disconnect()
                self.connection_state = -1
                print '[INFO] %s tried to join full server' % self.address.host
                return

        self.packet_handlers = {
            ClientVersion.packet_id: self.on_version_packet,
            EntityUpdate.packet_id: self.on_entity_packet,
            ClientChatMessage.packet_id: self.on_chat_packet,
            InteractPacket.packet_id: self.on_interact_packet,
            HitPacket.packet_id: self.on_hit_packet,
            ShootPacket.packet_id: self.on_shoot_packet
        }

        self.packet_handler = PacketHandler(CS_PACKETS, self.on_packet)

        server.connections.add(self)
        self.rights = AttributeSet()

        self.scripts = ScriptManager()
        server.scripts.call('on_new_connection', connection=self)

    def dataReceived(self, data):
        self.packet_handler.feed(data)

    def disconnect(self, reason=None):
        self.transport.loseConnection()
        self.connectionLost(reason)

    def connectionLost(self, reason):
        if self.connection_state < 0:
            return
        self.server.connections.discard(self)
        if self.connection_state >= 3:
            del self.server.players[self]
            print '[INFO] Player %s #%s left the game.' % (self.name, self.entity_id)
            self.server.send_chat('<<< %s #%s left the game' % (self.name, self.entity_id))
        self.connection_state = -1
        if self.entity_id is not None:
            self.server.world.unregister(self.entity_id)
            self.server.entity_ids.put_back(self.entity_id)
        if self.scripts is not None:
            self.scripts.unload()

    # packet methods

    def send_packet(self, packet):
        self.transport.write(write_packet(packet))

    def on_packet(self, packet):
        if self.connection_state < 0:
            return
        if packet is None:
            print 'Invalid packet received'
            self.disconnect()
            raise StopIteration()
        handler = self.packet_handlers.get(packet.packet_id, None)
        if handler is None:
            # print 'Unhandled client packet: %s' % packet.packet_id
            return
        handler(packet)

    def on_version_packet(self, packet):
        if packet.version != constants.CLIENT_VERSION:
            mismatch_packet.version = constants.CLIENT_VERSION
            self.send_packet(mismatch_packet)
            self.disconnect(None)
            return
        server = self.server
        self.entity_id = server.entity_ids.pop()
        join_packet.entity_id = self.entity_id
        self.connection_state = 2
        self.send_packet(join_packet)
        seed_packet.seed = server.config.base.seed
        self.send_packet(seed_packet)

    def on_entity_packet(self, packet):
        if self.entity_data is None:
            self.entity_data = create_entity_data()
        mask = packet.update_entity(self.entity_data)
        self.entity_data.mask |= mask
        if self.connection_state==2 and getattr(self.entity_data, 'name', None):
            self.on_join()
            return

        self.scripts.call('on_entity_update', mask=mask)
        # XXX clean this up
        if entity.is_pos_set(mask):
            self.on_pos_update()
        if entity.is_mode_set(mask):
            self.scripts.call('on_mode_update')
        if entity.is_class_set(mask):
            self.scripts.call('on_class_update')
        if entity.is_name_set(mask):
            self.scripts.call('on_name_update')
        if entity.is_multiplier_set(mask):
            self.scripts.call('on_multiplier_update')
        if entity.is_level_set(mask):
            self.scripts.call('on_level_update')
        if entity.is_equipment_set(mask):
            self.scripts.call('on_equipment_update')
        if entity.is_skill_set(mask):
            self.scripts.call('on_skill_update')
        if entity.is_appearance_set(mask):
            self.scripts.call('on_appearance_update')
        if entity.is_charged_mp_set(mask):
            self.scripts.call('on_charged_mp_update')
        if entity.is_flags_set(mask):
            self.scripts.call('on_flags_update')
        if entity.is_consumable_set(mask):
            self.scripts.call('on_consumable_update')

    def on_chunk(self, data):
        self.chunk = data

    def on_pos_update(self):
        if self.server.world:
            chunk = self.server.world.get_chunk_scaled(self.position.x, self.position.y)
            if chunk != self.chunk:
                self.chunk = chunk
                self.scripts.call('on_chunk_update')
        self.scripts.call('on_pos_update')

    def on_chat_packet(self, packet):
        message = filter_string(packet.value).strip()
        if not message:
            return
        message = self.on_chat(message)
        if not message:
            return
        chat_packet.entity_id = self.entity_id
        chat_packet.value = message
        self.server.broadcast_packet(chat_packet)
        print '[CHAT] %s: %s' % (self.name, message)

    def on_interact_packet(self, packet):
        interact_type = packet.interact_type
        item = packet.item_data
        if interact_type == INTERACT_DROP:
            pos = self.position.copy()
            pos.z -= constants.BLOCK_SCALE
            if self.scripts.call('on_drop', item=item,
                                 pos=pos).result is False:
                return
            self.server.drop_item(packet.item_data, pos)
        elif interact_type == INTERACT_PICKUP:
            try:
                item = self.server.remove_item(packet.chunk_x, packet.chunk_y, packet.item_index)
            except IndexError:
                return
            self.give_item(item)

    def on_hit_packet(self, packet):
        try:
            target = self.server.entities[packet.target_id]
        except KeyError:
            return
        if constants.MAX_DISTANCE > 0:
            edist = get_distance_3d(self.position.x,
                                    self.position.y,
                                    self.position.z,
                                    target.entity_data.pos.x,
                                    target.entity_data.pos.y,
                                    target.entity_data.pos.z)
            if edist > constants.MAX_DISTANCE:
                print '[ANTICHEAT BASE] Player %s tried to attack target that is %s away!' % (self.name, edist)
                self.kick('Range error')
                return
        if self.scripts.call('on_hit',
                             target=target,
                             packet=packet).result is False:
            return
        self.server.update_packet.player_hits.append(packet)
        if packet.damage <= 0:
            return
        if packet.damage > 1000:
            packet.damage = 1000
        if target.hp > packet.damage:
            if self.scripts.call('on_damage',
                                 target=target,
                                 packet=packet).result is False:
                return
            target.hp -= packet.damage
        else:
            target.hp = 0
            self.scripts.call('on_kill', target=target)

    def on_shoot_packet(self, packet):
        self.server.update_packet.shoot_actions.append(packet)

    def do_anticheat_actions(self):
        if not self.server.config.base.cheat_prevention:
            return False
        if not self.check_name():
            return True
        if not self.check_pos():
            return True
        self.last_pos = self.position
        if self.entity_data.entity_type < constants.ENTITY_TYPE_PLAYER_MIN_ID or self.entity_data.entity_type > constants.ENTITY_TYPE_PLAYER_MAX_ID:
            print '[ANTICHEAT BASE] Player %s tried to join with invalid entity type id: %s!' % (self.name, self.entity_data.entity_type)
            self.kick('Invalid entity type submitted')
            return True
        if self.entity_data.class_type < constants.ENTITY_CLASS_PLAYER_MIN_ID or self.entity_data.class_type > constants.ENTITY_CLASS_PLAYER_MAX_ID :
            self.kick('Invalid character class submitted')
            print '[ANTICHEAT BASE] Player %s tried to join with an invalid character class! Kicked.' % self.name
            return True
        if self.entity_data.hp > 1000:
            self.kick('Abnormal health points submitted')
            print '[ANTICHEAT BASE] Player %s tried to join with an abnormal health points! Kicked.' % self.name
            return True
        if self.entity_data.level < 1 or self.entity_data.level > constants.PLAYER_MAX_LEVEL:
            self.kick('Abnormal level submitted')
            print '[ANTICHEAT BASE] Player %s tried to join with an abnormal character level! Kicked.' % self.name
            return True
        # This seems to filter prevent cheaters from joining
        needed_xp = get_needed_total_xp(self.entity_data.level)
        if needed_xp > self.entity_data.current_xp:
            self.kick('Invalid character level')
            print '[ANTICHEAT BASE] Player %s tried to join with character level %s that is higher than total xp needed (%s/%s)! Kicked.' % (self.name, self.entity_data.level, self.entity_data.current_xp, needed_xp)
            return True
        #if self.entity_data.inventory...... in constants.FORBIDDEN_ITEMS_POSSESSION
        return False


    # handlers

    def on_join(self):
        if self.connection_state < 0:
            print '[WARNING] Connection of %s [%s] already has been invalidated before!' % (self.name, self.address.host)
            self.kick('Blocked join')
            return
        if self.connection_state != 2:
            print '[WARNING] Player %s [%s] tried to join in invalid state!' % (self.name, self.address.host)
            self.kick('Invalid state')
            return
        if self.check_name() is False:
            self.kick('Bad name')
            return
        # Call join script
        res = self.scripts.call('on_join').result
        if res is False:
            self.kick('Blocked join')
            print '[WARNING] Joining client %s blocked by script!' % self.address.host
            return
        if self.entity_data.level < self.server.config.base.join_level_min:
            print '[WARNING] Level of player %s [%s] is lower than minimum of %s' % (self.name, self.address.host, self.server.config.base.join_level_min)
            self.kick('Your level has to be at least %s' % self.server.config.base.join_level_min)
            return
        if self.entity_data.level > self.server.config.base.join_level_max:
            print '[WARNING] Level of player %s [%s] is higher than maximum of %s' % (self.name, self.address.host, self.server.config.base.join_level_max)
            self.kick('Your level has to be lower than %s' % self.server.config.base.join_level_max)
            return
        self.last_pos = self.position
        # we dont want cheaters being able joining the server
        if self.do_anticheat_actions():
            self.server.send_chat('[ANTICHEAT] Player %s (%s) has been kicked for cheating.' % (self.name,
                                                                                                get_entity_type_level_str(self.entity_data)))
            return
        print '>>> Player %s %s #%s [%s] joined the game' % (self.name,
                                                             get_entity_type_level_str(self.entity_data),
                                                             self.entity_id,
                                                             self.address.host)
        self.server.send_chat('>>> %s #%s (%s) joined the game' % (self.name,
                                                                   self.entity_id,
                                                                   get_entity_type_level_str(self.entity_data)))
        # connection successful -> continue
        for player in self.server.players.values():
            entity_packet.set_entity(player.entity_data, player.entity_id)
            self.send_packet(entity_packet)
        self.server.players[(self.entity_id,)] = self
        self.connection_state = 3

    def on_command(self, command, parameters):
        self.scripts.call('on_command', command=command, args=parameters)
        if ( (not parameters) or (command == 'register') or (command == 'login') ):
            print '[COMMAND] %s: /%s' % (self.name, command)
        else:
            print '[COMMAND] %s: /%s %s' % (self.name, command, ' '.join(parameters))

    def on_chat(self, message):
        if self.time_last_chat < int(reactor.seconds() - constants.ANTISPAM_LIMIT_CHAT):
            self.chat_messages_burst = 0
        else:
            if self.chat_messages_burst < constants.ANTISPAM_BURST_CHAT:
                self.chat_messages_burst += 1
            else:
                self.time_last_chat = reactor.seconds()
                res = self.scripts.call('on_spamming_chat').result
                if not res:
                    # As we do not want to spam back only do this when
                    # burst limit is reached for the first time
                    if self.chat_messages_burst == constants.ANTISPAM_BURST_CHAT:
                        if self.server.config.base.auto_kick_spam:
                            self.kick('Kicked for chat spamming')
                        else:
                            self.send_chat('[ANTISPAM] Please do not spam in chat!')
                return
        if message.startswith('/'):
            command, args = parse_command(message[1:])
            self.on_command(command, args)
            return
        event = self.scripts.call('on_chat', message=message)
        if event.result is False:
            return
        return event.message

    # other methods

    def send_chat(self, value):
        packet = ServerChatMessage()
        packet.entity_id = 0
        packet.value = value
        self.send_packet(packet)

    def give_item(self, item):
        action = PickupAction()
        action.entity_id = self.entity_id
        action.item_data = item
        self.server.update_packet.pickups.append(action)

    def send_lines(self, lines):
        current_time = 0
        for line in lines:
            reactor.callLater(current_time, self.send_chat, line)
            current_time += 2

    def heal(self, amount=None, reason=None):
        if (amount is not None and amount <= 0) or (hp >= constants.PLAYER_MAX_HEALTH):
            return False
        if self.scripts.call('on_heal', amount, reason).result is False:
            return False
        if amount is None or amount + hp > constants.PLAYER_MAX_HEALTH:
            self.entity_data.hp = constants.PLAYER_MAX_HEALTH
        else:
            self.entity_data.hp += amount
        self.entity_data.changed = True
        for connection in self.server.connections.values():
            entity_packet.set_entity(self.entity_data, self.entity_id)
            connection.send_packet(entity_packet)
        if reason is None:
            self.send_chat('[INFO] You have been healed.')
        elif reason is not False:
            self.send_chat(reason)

    def damage(self, damage=0, critical=0, stun_duration=0, reason=None):
        if self.scripts.call('on_damage', damage, critical, stun_duration, reason).result is False:
            return False
        packet = HitPacket()
        packet.entity_id = self.entity_id
        packet.target_id = self.entity_id
        packet.hit_type = HIT_NORMAL
        packet.damage = damage
        packet.critical = critical
        packet.stun_duration = stun_duration
        packet.something8 = 0
        packet.pos = self.position
        packet.hit_dir = Vector3()
        packet.skill_hit = 0
        packet.show_light = 0
        # Processed by the server and clients in next update task run
        self.server.update_packet.player_hits.append(packet)
        self.entity_data.changed = True
        if reason:
            self.send_chat(reason)
        return True

    def kill(self, killer=None, reason=None):
        if not damage(self.entity_data.hp + 100, 1, 0):
            return False
        if self.scripts.call('on_kill', killer=killer, reason=reason).result is False:
            return False
        packet = KillAction()
        if killer is None:
            packet.entity_id = self.entity_id
        else:
            packet.entity_id = killer.entity_id
        packet.target_id = self.entity_id
        packet.xp_gained = 0
        # Processed by the server and clients in next update task run
        self.server.update_packet.kill_actions.append(packet)
        self.entity_data.changed = True
        if reason is None:
            if killer is self:
                self.send_chat('You commited suicide')
            else:
                self.send_chat('You have been killed by %s' % killer.entity_data.name)
        elif reason is not False:
            self.send_chat(reason)
        return True

    def kick(self, reason=None):
        res = self.scripts.call('on_kick', reason=reason)
        if res is False:
            return
        if reason is None:
            self.send_chat('You have been kicked')
        elif reason is not False:
            self.send_chat(reason)
        self.disconnect()
        if self.entity_data.name:
            self.server.send_chat('<<< %s has been kicked' % self.entity_data.name)

    def teleport(self, to_x, to_y, to_z):
        res = self.scripts.call('on_teleport', pos=self.position)
        if res is False:
            return
        self.entity_data.pos.x = to_x
        self.entity_data.pos.y = to_y
        self.entity_data.pos.z = to_z
        # To not confuse anti cheating system
        self.last_pos = self.position
        self.entity_data.changed = True
        for connection in self.server.connections.values():
            entity_packet.set_entity(self.entity_data, self.entity_id)
            connection.send_packet(entity_packet)
        self.send_chat('[INFO] You have been teleported.')

    def check_name(self):
        if self.old_name is None:
            return True
        if not self.name:
            self.kick('No name')
            print '[WARNING] %s had no name! Kicked.' % self.address.host
            return False
        if len(self.name) > constants.NAME_LENGTH_MAX:
            self.kick('Name to long')
            print '[WARNING] %s had name longer than %s characters! Kicked.' % (self.address.host, constants.NAME_LENGTH_MAX)
            return False
        self.entity_data.name = self.name.strip()
        if len(self.name) < constants.NAME_LENGTH_MIN:
            self.kick('Name to short')
            print '[WARNING] %s had name shorter than %s characters! Kicked.' % (self.address.host, constants.NAME_LENGTH_MIN)
            return False
        if re.search(self.server.config.base.name_filter, self.name) is None:
            self.kick('Illegal name')
            print '[WARNING] %s had illegal name! Kicked.' % self.address.host
            return False
        return True

    def check_pos(self):
        if self.old_pos is not None:
            if (self.position.x == self.old_pos.x) and (self.position.y == self.old_pos.y) and (self.position.z == self.old_pos.z):
                return True
            server = self.server
            cpres = self.scripts.call('on_pos_update').result
            if cpres is False:
                self.entity_data.x = self.old_pos.x
                self.entity_data.y = self.old_pos.y
                return True
            # check new coordinates and distances
            edist = get_distance_3d(self.old_pos.x,
                                    self.old_pos.y,
                                    self.old_pos.z,
                                    self.position.x,
                                    self.position.y,
                                    self.position.z)
            if edist > (reactor.seconds() * constants.MAX_MOVE_DISTANCE):
                self.entity_data.x = self.old_pos.x
                self.entity_data.y = self.old_pos.y
                self.entity_data.z = self.old_pos.z
                print 'Player %s moved to fast!' % self.name
                return False
            cxo = math.floor(self.old_pos.x / constants.CHUNK_SCALE)
            cyo = math.floor(self.old_pos.y / constants.CHUNK_SCALE)
            cxn = math.ceil(self.position.x / constants.CHUNK_SCALE)
            cyn = math.ceil(self.position.y / constants.CHUNK_SCALE)
            if (cxo != cxn) or (cyo != cyn):
                self.server.world.move_locatable(self.entity_id, self.position.x, self.position.y, self.position.z)
                print '%s entered chunk (%s,%s)' % (self.name, cxn, cyn)
        self.old_pos = self.position
        return True

    def check_items(self):
        server = self.server
        for slotindex in range(13):
            item = entity_data.equipment[slotindex]
            if not item or item.type == 0:
                continue
            if item.level < 0:
                self.kick('Illegal item')
                print '[INFO] Player %s #%s (%s) [%s] had item with level lover than 0' % (self.entity_data.name, self.entity_id, get_entity_type_level_str(self.entity_data), self.address.host)
                return False
            if item.material in self.server.config.base.forbid_item_possession:
                self.kick('Forbidden item')
                print '[INFO] Player %s #%s (%s) [%s] had forbidden item #%s' % (self.entity_data.name, self.entity_id, get_entity_type_level_str(self.entity_data), self.address.host, item.material)
                return False
        return True

    # convienience methods

    @property
    def position(self):
        if not self.entity_data.pos:
            return Vector3()
        return Vector3(self.entity_data.pos.x,
                       self.entity_data.pos.y,
                       self.entity_data.pos.z)


    @property
    def name(self):
        if not self.entity_data.name:
            return None
        return self.entity_data.name


class CubeWorldServer(Factory):
    items_changed = False
    exit_code = 0
    last_secondly_check = None
    updates_since_last_second = 0
    updates_per_second = 0
    current_change_index = 0
    world = None

    def __init__(self, config):
        self.config = config
        base = config.base

        # GAME RELATED
        self.update_packet = ServerUpdate()
        self.update_packet.reset()

        self.connections = set()
        self.players = MultikeyDict()

        self.entities = {}
        self.entity_ids = IDPool(1)

        # DATABASE
        self.db_con = database.get_connection()
        database.create_structure(self.db_con)

        # Initialize default world
        self.world = World(self)

        self.update_loop = LoopingCall(self.update)
        self.update_loop.start(1.0 / constants.UPDATE_FPS, False)

        # SERVER RELATED
        self.git_rev = base.get('git_rev', None)

        self.ranks = {}
        for k, v in base.ranks.iteritems():
            self.ranks[k.lower()] = v

        self.scripts = ScriptManager()
        for script in base.scripts:
            self.load_script(script)

        # INGAME TIME
        self.extra_elapsed_time = 0.0
        self.start_time = reactor.seconds()
        self.set_clock('12:00')

        # START LISTENING
        self.listen_tcp(base.port, self)

    def buildProtocol(self, addr):
        con_remain = self.config.base.max_connections_per_ip
        for connection in self.connections:
            if connection.address.host == addr.host:
                con_remain -= 1
                if con_remain <= 0:
                    if con_remain == 0:
                        print '[WARNING] Too many connections from %s, closing...' % addr.host
                    connection.disconnect()
        if con_remain <= 0:
            return
        self.db_con = database.get_connection()
        if database.is_banned_ip(self.db_con, addr.host):
            print '[INFO] Banned client %s tried to join.' % addr.host
            return 'You are banned from this server.'
        if self.scripts.call('on_connection_attempt', address=addr).result is False:
            print '[WARNING] Connection attempt for %s blocked by script!' % addr.host
            return False
        return CubeWorldConnection(self, addr)

    def remove_item(self, chunk_x, chunk_y, index):
        print '[DEBUG] Removing item #%s from chunk %s,%s' % (index, chunk_x, chunk_y)
        chunk = self.world.get_chunk_unscaled(chunk_x, chunk_y)
        ret = chunk.item_list.pop(index)
        self.items_changed = True
        return ret.item_data

    def drop_item(self, item_data, pos):
        print '[DEBUG] Dropping item at %s,%s' % (pos.x, pos.y)
        chunk = self.world.get_chunk_scaled(pos.x, pos.y)
        if len(chunk.item_list) > constants.MAX_ITEMS_PER_CHUNK:
            print '[WARNING] To many items at Chunk(%s,%s)!' % (math.floor(pos.x / constants.CHUNK_SCALE), math.floor(pos.y / constants.CHUNK_SCALE))
            return False
        item = ChunkItemData()
        item.drop_time = 750
        item.scale = 0.1
        item.rotation = 185.0
        item.something3 = item.something5 = item.something6 = 0
        item.pos = pos
        item.item_data = item_data
        chunk.item_list.append(item)
        self.items_changed = True

    def update(self):
        self.scripts.call('update')

        uxtime = reactor.seconds()
        if self.last_secondly_check:
            update_seconds_delta = uxtime - self.last_secondly_check
        else:
            update_seconds_delta = 0

        if update_seconds_delta < 1:
            self.updates_since_last_second += 1
        else:
            ups = math.floor((self.updates_per_second + (self.updates_since_last_second / update_seconds_delta)) / 2)
            self.updates_since_last_second = 0
            if ups != self.updates_per_second:
                dus = ups - self.updates_per_second
                self.updates_per_second = ups
                if dus > 0:
                    print "\rUpdates/s: %s (+%s)" % (ups, dus)
                elif dus < 0:
                    print "\rUpdates/s: %s (-%s)" % (ups, dus)
            for player in self.players.values():
                if player.packet_count > 0:
                    ppr = math.ceil( ( player.packet_rate + ( player.packet_count / update_seconds_delta ) ) / 2 )
                    player.packet_count = 0
                    if ppr != player.packet_rate:
                        dpr = ppr - player.packet_rate
                        player.packet_rate = ppr
                        if dpr > 0:
                            print "\rPackets/s for %s: %s (+%s)" % (player.name, player.packet_rate, dpr)
                        elif dpr < 0:
                            print "\rPackets/s for %s: %s (-%s)" % (player.name, player.packet_rate, dpr)

        # entity updates
        for entity_id, entity in self.entities.iteritems():
            entity_packet.set_entity(entity, entity_id, entity.mask)
            entity.mask = 0
            self.broadcast_packet(entity_packet)
        self.broadcast_packet(update_finished_packet)

        # other updates
        update_packet = self.update_packet
        if self.items_changed:
            for chunk in self.world.chunks.values():
                item_list = ChunkItems()
                item_list.chunk_x = chunk.chunk_x
                item_list.chunk_y = chunk.chunk_y
                item_list.items = chunk.item_list
                update_packet.chunk_items.append(item_list)
                for item in chunk.item_list:
                    item.drop_time = 0
            self.items_changed = False
        self.broadcast_packet(update_packet)
        update_packet.reset()

        if update_seconds_delta != 0:
            for player in self.players.values():
                if player.time_last_packet >= (uxtime - constants.CLIENT_RECV_TIMEOUT):
                    if player.entity_data.changed:
                        player.entity_data.changed = False
                        ret = player.do_anticheat_actions()
                        if (not ret) and player.login_id:
                            database.update_player(self.db_con, player.login_id, player.name)
                else:
                    print '[WARNING] Connection timed out for Player %s #%s' % (player.entity_data.name, player.entity_id)
                    player.kick('Connection timed out')
        self.broadcast_time()

    def hit_entity_id(self, id):
        return True

    def send_chat(self, value):
        packet = ServerChatMessage()
        packet.entity_id = 0
        packet.value = value
        self.broadcast_packet(packet)

    def broadcast_packet(self, packet):
        data = write_packet(packet)
        for player in self.players.values():
            player.transport.write(data)

    def broadcast_time(self):
        time_packet.time = self.get_time()
        time_packet.day = self.get_day()
        self.broadcast_packet(time_packet)

    # line/string formatting options based on config

    def format(self, value):
        format_dict = {'server_name': self.config.base.server_name}
        return value % format_dict

    def format_lines(self, value):
        lines = []
        for line in value:
            lines.append(self.format(line))
        return lines

    # script methods

    def load_script(self, name):
        try:
            mod = __import__('scripts.%s' % name, globals(), locals(), [name])
        except ImportError, e:
            traceback.print_exc(e)
            return None
        script = mod.get_class()(self)
        print '[INFO] Loaded script %r' % name
        return script

    def call_command(self, user, command, args):
        """
        Calls a command from an external interface, e.g. IRC, console
        """
        return self.scripts.call('on_command', user=user, command=command,
                                 args=args).result

    def get_mode(self):
        return self.scripts.call('get_mode').result

    # command convenience methods (for /help)

    def get_commands(self):
        for script in self.scripts.get():
            if script.commands is None:
                continue
            for command in script.commands.itervalues():
                yield command

    def get_command(self, name):
        for script in self.scripts.get():
            if script.commands is None:
                continue
            command = script.commands.get(name, None)
            if command:
                return command

    # data store methods

    def load_data(self, name, default=None):
        return database.load_data(self.db_con, name, default)

    def save_data(self, name, value):
        return database.save_data(self.db_con, name, value)


    # time methods

    def set_clock(self, value):
        day = self.get_day()
        time = parse_clock(value)
        self.start_time = reactor.seconds()
        self.extra_elapsed_time = day * constants.MAX_TIME + time

    def get_elapsed_time(self):
        dt = reactor.seconds() - self.start_time
        dt *= self.config.base.time_modifier * constants.NORMAL_TIME_SPEED
        return dt * 1000 + self.extra_elapsed_time

    def get_time(self):
        return int(self.get_elapsed_time() % constants.MAX_TIME)

    def get_day(self):
        return int(self.get_elapsed_time() / constants.MAX_TIME)

    def get_clock(self):
        return get_clock_string(self.get_time())

    # stop/restart

    def stop(self, code=None):
        self.exit_code = code
        reactor.stop()

    # twisted wrappers

    def listen_udp(self, *arg, **kw):
        interface = self.config.base.network_interface
        return reactor.listenUDP(*arg, interface=interface, **kw)

    def listen_tcp(self, *arg, **kw):
        interface = self.config.base.network_interface
        return reactor.listenTCP(*arg, interface=interface, **kw)

    def connect_tcp(self, *arg, **kw):
        interface = self.config.base.network_interface
        return reactor.connectTCP(*arg, bindAddress=(interface, 0), **kw)


def main():
    # for py2exe
    if hasattr(sys, 'frozen'):
        path = os.path.dirname(unicode(sys.executable,
                                       sys.getfilesystemencoding()))
        root = os.path.abspath(os.path.join(path, '..'))
        sys.path.append(root)

    config = ConfigObject('./config')
    server = CubeWorldServer(config)

    print '[INFO] Server is listening on port %s' % config.base.port

    if config.base.profile_file is None:
        reactor.run()
    else:
        import cProfile
        cProfile.run('reactor.run()', filename=config.base.profile_file)

    database.close_connection(server.db_con)

    sys.exit(server.exit_code)

if __name__ == '__main__':
    main()
