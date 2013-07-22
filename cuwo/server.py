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
                         get_chunk, filter_string,
                         get_needed_total_xp, get_power_level,
                         get_player_class_str, get_player_race_str)
from cuwo.script import call_scripts
from cuwo import database

import collections
import imp
import os
import sys
import json
import random


# initialize packet instances for sending
join_packet = JoinPacket()
seed_packet = SeedData()
chat_packet = ServerChatMessage()
entity_packet = EntityUpdate()
update_finished_packet = UpdateFinished()
time_packet = CurrentTime()
mismatch_packet = ServerMismatch()
server_full_packet = ServerFull()


class CubeWorldConnection(Protocol):
    """
    Protocol used for players
    """
    connection_state = 0
    player_id = None
    entity_id = None
    entity_data = None
    disconnected = False
    change_index = -1

    last_health = -1
    last_level = -1
    last_xp = -1

    # used for anti chat spamming
    time_last_chat    = -1
    chat_messages_burst = 0

    # used for detecting dead connections
    time_last_packet  = -1
    # used for basic DoS protection
    packet_burst = 0

    def __init__(self, server, addr):
        self.address = addr
        self.server = server

    # connection methods

    def connectionMade(self):
        self.packet_handlers = {
            ClientVersion.packet_id: self.on_version_packet,
            EntityUpdate.packet_id: self.on_entity_packet,
            ClientChatMessage.packet_id: self.on_chat_packet,
            InteractPacket.packet_id: self.on_interact_packet,
            HitPacket.packet_id: self.on_hit_packet,
            ShootPacket.packet_id: self.on_shoot_packet
        }
        self.scripts = []
        self.server.call_scripts('on_new_connection', self)
        self.packet_handler = PacketHandler(CS_PACKETS, self.on_packet)
        self.rights = AttributeSet()

    def dataReceived(self, data):
        self.packet_handler.feed(data)

    def disconnect(self, reason=None):
        self.time_disconnected = self.server.last_secondly_check
        self.transport.loseConnection()
        self.connectionLost(reason)

    def connectionLost(self, reason=None):
        try:
            del self.server.connections[self]
        except KeyError:
            pass
        finally:
            if self.connection_state == 0:
                return
            self.connection_state = 0
            self.call_scripts('on_connection_lost')
            if not (self.entity_id is None):
                try:
                    del self.server.entities[self.entity_id]
                except KeyError:
                    pass
                else:
                    self.server.entity_ids.put_back(self.entity_id)
            for script in self.scripts[:]:
                script.unload()
            if self.connection_state > 0:
                self.connection_state = 0
                print '[INFO] Player %s #%s (%s) [%s] left the game.' % (self.name,
                                                                            self.player_id,
                                                                            common.get_entity_type_level_str(self.entity_data),
                                                                            self.address.host)
                self.server.send_chat('<<< %s (%s) left the game' % (self.name,
                                                                     sommon.get_entity_type_level_str(self.entity_data))


    # packet methods

    def send_packet(self, packet):
        self.transport.write(write_packet(packet))

    def on_packet(self, packet):
        self.time_last_packet = self.server.last_secondly_check
        handler = self.packet_handlers.get(packet.packet_id, None)
        if handler is None:
            print '[WARNING] Unhandled client packet for player %s #%s [%s]'
                  % (self.name,
                     self.player_id,
                     self.address.host,
                     packet.packet_id)
        return
        # packets are normally sent at least once per second by the client
        handler(packet)

    def on_version_packet(self, packet):
        if packet.version != constants.CLIENT_VERSION:
            res = self.call_scripts('on_wrong_version_join')
            if not res:
                mismatch_packet.version = constants.CLIENT_VERSION
                self.send_packet(mismatch_packet)
                self.disconnect(None)
                print '[INFO] Player %s #%s (%s) [%s] is using an incompatible client version (%s != %s)'
                      % (self.name,
                         self.player_id,
                         common.get_entity_type_level_str(self.entity_data)),
                         self.address.host,
                         packet.version,
                         constants.CLIENT_VERSION)
                return
        if len(self.server.connections) >= self.server.config.max_players:
            res = self.call_scripts('on_join_full_server')
            # For being able to allow joining by external scritps when server is full
            if not res:
                self.send_packet(server_full_packet)
                self.disconnect(None)
                print '[INFO] Player %s [%s] tried to join full server'
                      % (self.name,
                         self.address.host)
            else:
                self.entity_id = self.server.entity_ids.pop()
                self.server.connections[(self.entity_id,)] = self
                join_packet.entity_id = self.entity_id
                self.send_packet(join_packet)
                seed_packet.seed = self.server.config.seed
                self.send_packet(seed_packet)

    def on_entity_packet(self, packet):
        if self.entity_data is None:
            self.entity_data = create_entity_data()
        self.server.entities[self.entity_id] = self.entity_data
        mask = self.entity_data.mask
        mask |= packet.update_entity(self.entity_data)
        if self.entity_data.entity_type >= constants.ENTITY_TYPE_PLAYER_MIN_ID and self.entity_data.entity_type <= constants.ENTITY_TYPE_PLAYER_MAX_ID and getattr(self.entity_data, 'name', None):
            if self.connection_state == 0:
                self.on_join()
        if is_bit_set(mask, 9):
            self.call_scripts('on_mode_update')
        if is_bit_set(mask, 21):
            self.call_scripts('on_class_update')
        if is_bit_set(mask, 30):
            self.call_scripts('on_multiplier_update')
        if is_bit_set(mask, 33):
            self.call_scripts('on_level_update')
        if is_bit_set(mask, 44):
            self.call_scripts('on_equipment_update')
        if is_bit_set(mask, 45):
            self.call_scripts('on_name_update')
        if is_bit_set(mask, 46):
            self.call_scripts('on_skill_update')

    def on_chat_packet(self, packet):
        # Spammer stopped for a defined amount of seconds - reset spam score
        if self.time_last_chat < (self.last_secondly_check - constants.ANTISPAM_LIMIT_CHAT):
            self.chat_messages_burst = 0
        # When spammer continues with spamming, antichat time also increases
        self.time_last_chat = self.last_secondly_check
        message = filter_string(packet.value).strip()
        if not message:
            return
        if not self.on_chat(message):
            return
        if self.chat_messages_burst < constants.ANTISPAM_BURST_CHAT:
            chat_packet.entity_id = self.entity_id
            chat_packet.value = message
            self.server.broadcast_packet(chat_packet)
            print '%s: %s' % (self.name, message)
        else:
            res = self.call_scripts('on_spamming_chat')
            if not res:
                self.chat_messages_burst += 1
                # As we do not want to spam back only do this when
                # burst limit is reached for the first time
                if self.chat_messages_burst == constants.ANTISPAM_BURST_CHAT:
                    if config.auto_kick_spam:
                        self.kick('Kicked for chat spamming')
                    else:
                    self.send_chat('[ANTISPAM] Please do not spam in chat!')
            else:
                # When a script allowed spamming reset burst limit
                self.chat_messages_burst = 0

    def on_interact_packet(self, packet):
        interact_type = packet.interact_type
        if interact_type == INTERACT_DROP:
            pos = self.position.copy()
            pos.z -= constants.BLOCK_SCALE
            item = packet.item_data
            if not self.call_scripts('on_drop', item, pos) is False:
                self.server.drop_item(item, pos)
        elif interact_type == INTERACT_PICKUP:
            res = self.call_scripts('on_pickup')
            if res is False:
                return
            chunk = (packet.chunk_x, packet.chunk_y)
            try:
                item = self.server.remove_item(chunk, packet.item_index)
                self.give_item(item)
                print '[DEBUG] Player %s picked up item #%s at chunk (%r,%r)' % (self.name, packet.item_index, packet.chunk_x, packet.chunk_y)
            except KeyError:
                print '[DEBUG] Exception while %s tried to interact with #%s at chunk (%r,%r)' % (self.name, packet.item_index, packet.chunk_x, packet.chunk_y)
        else:
            print '[DEBUG] Player %s interacted with unimplemented type %s, id %s, packet index %s at pos (%r,%r)' % (self.name, interact_type, self.entity_id, packet.item_index, packet.chunk_x, packet.chunk_y)

    def on_hit_packet(self, packet):
        try:
            target = self.server.entities[packet.target_id]
        except KeyError:
            return
        if constants.MAX_HIT_DISTANCE > 0:
            edist = common.get_distance_3d(self.entity_data.x,
                                           self.entity_data.y,
                                           self.entity_data.z,
                                           target.entity_data.x,
                                           target.entity_data.y,
                                           target.entity_data.z)
            if edist > constants.MAX_HIT_DISTANCE:
                return
        res = self.call_scripts('on_hit', target, packet.damage)
        if res is False:
            return
        self.server.update_packet.player_hits.append(packet)
        if packet.damage <= 0:
            return
        if target.hp <= 0:
            target.hp = 0
            return
        if packet.damage > 1000:
            packet.damage = 1000
        if target.hp > packet.damage:
            res = self.call_scripts('on_damage', target, packet.damage)
            if res is False or res <= 0:
                return
            target.hp -= packet.damage
        else:
            target.hp = 0
            self.call_scripts('on_kill', target)


    def on_shoot_packet(self, packet):
        self.server.update_packet.shoot_actions.append(packet)


    def do_anticheat_actions(self):
        if not constants.ANTICHEAT_SYSTEM_ENABLED:
            return False
        if self.entity_data.entity_type < constants.ENTITY_TYPE_PLAYER_MIN_ID or self.entity_data.entity_type > constants.ENTITY_TYPE_PLAYER_MAX_ID:
            print '[ANTICHEAT] Player %s tried to join with invalid entity type id: %s!' % (self.entity_data.name, self.entity_data.entity_type)
            self.kick('Invalid entity type submitted')
            return True
        if self.entity_data.class_type < constants.ENTITY_CLASS_PLAYER_MIN_ID or self.entity_data.class_type > constants.ENTITY_CLASS_PLAYER_MAX_ID :
            self.kick('Invalid character class submitted')
            print '[ANTICHEAT] Player %s tried to join with an invalid character class! Kicked.' % self.entity_data.name
            return True
        if self.entity_data.hp > 1000:
            self.kick('Abnormal health points submitted')
            print '[ANTICHEAT] Player %s tried to join with an abnormal health points! Kicked.' % self.entity_data.name
            return True
        if self.entity_data.level < 1 or self.entity_data.level > constants.PLAYER_MAX_LEVEL:
            self.kick('Abnormal level submitted')
            print '[ANTICHEAT] Player %s tried to join with an abnormal character level! Kicked.' % self.entity_data.name
            return True
        # This seems to filter prevent cheaters from joining
        needed_xp = get_needed_total_xp(self.entity_data.level)
        if needed_xp > self.entity_data.current_xp:
            self.kick('Invalid character level')
            print '[ANTICHEAT] Player %s tried to join with character level %s that is higher than total xp needed for it (%s/%s)! Kicked.' % (self.entity_data.name, self.entity_data.level, self.entity_data.current_xp, needed_xp)
            return True
        #if self.entity_data.inventory...... in constants.FORBIDDEN_ITEMS_POSSESSION
        return False


    # handlers

    def on_join(self):
        if self.connection_state != 0:
            self.kick('Tried to join more than once!')
            return
        # lock
        self.connection_state = 5
        if self.entity_data.level < config.join_level_min:
            print '[INFO] Level of player %s #%s (%s) [%s] is lower than minimum of %s' % (self.entity_data.name, self.entity_id, common.get_entity_type_level_str(self.entity_data), self.address.host, config.join_level_min)
            self.kick('Your level has to be at least %s' % config.join_level_min)
            return
        if self.entity_data.level > config.join_level_max:
            print '[INFO] Level of player %s #%s (%s) [%s] is higher than maximum of %s' % (self.entity_data.name, self.entity_id, common.get_entity_type_level_str(self.entity_data), self.address.host, config.join_level_max)
            self.kick('Your level has to be lower than %s' % config.join_level_max)
            return
        # we dont want cheaters being able joining the server
        if self.do_anticheat_actions():
            self.connection_state = -3
            self.server.send_chat('[ANTICHEAT] Player %s (%s) has been kicked for cheating.' % (self.entity_data.name,
                                                                                                common.get_entity_type_level_str(self.entity_data)))
        else:
            # Call join script
            self.call_scripts('on_join')
            print '[INFO] Player %s #%s (%s) [%s] joined the game' % (self.entity_data.name,
                                                                      common.get_entity_type_level_str(self.entity_data),
                                                                      self.entity_id,
                                                                      self.address.host)
            for connection in self.server.connections.values():
                entity_packet.set_entity(connection.entity_data, connection.entity_id)
                self.send_packet(entity_packet)
            self.server.send_chat('>>> %s (%s) joined the game' % (self.entity_data.name
                                                                   common.get_entity_type_level_str(self.entity_data)))
            self.connection_state = 1

    def on_command(self, command, parameters):
        self.call_scripts('on_command', command, parameters)

    def on_chat(self, message):
        if message.startswith('/'):
            command, args = parse_command(message[1:])
            self.on_command(command, args)
            self.send_chat('[COMMAND] %s' % command)
            print '[COMMAND] %s: /%s' % (self.name, command)
            return False
        res = self.call_scripts('on_chat', message)
        return True

    def on_equipment_update(self):
        # TODO
        return True

    def on_level_update(self):
        # TODO
        return True

    def on_skill_update(self):
        # TODO
        return True


    # other methods

    def send_chat(self, value):
        packet = ServerChatMessage()
        packet.entity_id = 0
        packet.value = value
        self.send_packet(packet)

    def give_item(self, item):
        res = self.server.call_scripts('on_before_giving_item', item)
        if res is False:
            return False
        action = PickupAction()
        action.entity_id = self.entity_id
        action.item_data = item

        # Processed by the server and clients in next update task run
        self.server.update_packet.pickups.append(action)
        self.entity_data.changed = True

    def send_lines(self, lines):
        current_time = 0
        for line in lines:
            reactor.callLater(current_time, self.send_chat, line)
            current_time += 2

    def heal(self, amount=None, reason=None):
        if (amount is not None and amount <= 0) or (hp >= constants.PLAYER_MAX_HEALTH):
            return False
        res = self.server.call_scripts('on_heal', amount, reason)
        if res is False:
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
        res = self.server.call_scripts('on_damage', damage, critical, stun_duration, reason)
        if res is False:
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
        res = self.server.call_scripts('on_kill')
        if res is False:
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
                self.send_chat('+ You commited suicide')
            else:
                self.send_chat('+ You have been killed by %s' % killer.name)
        elif reason is not False:
            self.send_chat(reason)
        return True

    def kick(self, reason=None):
        res = self.call_scripts('on_kick')
        if res is False:
            return
        if reason is None:
            self.send_chat('You have been kicked')
        elif reason is not False:
            self.send_chat(reason)
        self.disconnect()
        if self.name:
            self.server.send_chat('<<< %s has been kicked' % self.name)

    def teleport(self, to_x, to_y, to_z):
        res = self.call_scripts('on_teleport')
        if res is False:
            return
        self.entity_data.x = to_x
        self.entity_data.y = to_y
        self.entity_data.z = to_z
        self.entity_data.changed = True
        for connection in self.server.connections.values():
            entity_packet.set_entity(self.entity_data, self.entity_id)
            connection.send_packet(entity_packet)
        self.send_chat('[INFO] You have been teleported.')

    def call_scripts(self, name, *arg, **kw):
        return call_scripts(self.scripts, name, *arg, **kw)


    # convienience methods

    @property
    def position(self):
        if self.entity_data is None:
            return None
        return Vector3(self.entity_data.x,
                       self.entity_data.y,
                       self.entity_data.z)


    @property
    def name(self):
        if self.entity_data is None:
            return None
        return getattr(self.entity_data, 'name', None)



class BanProtocol(Protocol):
    """
    Protocol used for banned players.
    Ignores data from client and only sends JoinPacket/ServerChatMessage
    """

    def __init__(self, message=None):
        self.message = message


    def send_packet(self, packet):
        self.transport.write(write_packet(packet))


    def connectionMade(self):
        join_packet.entity_id = 1
        self.send_packet(join_packet)
        self.disconnect_call = reactor.callLater(0.1, self.disconnect)


    def disconnect(self):
        if self.message is not None:
            chat_packet.entity_id = 0
            chat_packet.value = self.message
        self.send_packet(chat_packet)
        self.transport.loseConnection()


    def connectionLost(self, reason):
        if self.disconnect_call.active():
            self.disconnect_call.cancel()



class CubeWorldServer(Factory):
    items_changed = False

    last_secondly_check = -1
    next_items_autoremoval = -1
    ticks_since_last_second = -1
    ticks_per_second = -1
    current_change_index = 0

    def __init__(self, config):
        self.config = config

        self.db_con = database.get_connection()
        database.create_structure(self.db_con)

        # GAME RELATED
        self.update_packet = ServerUpdate()
        self.update_packet.reset()

        self.connections = MultikeyDict()

        self.entities = {}
        self.entity_ids = IDPool(1)

        self.chunk_items = collections.defaultdict(list)

        self.update_loop = LoopingCall(self.update)
        self.update_loop.start(1.0 / constants.UPDATE_FPS, False)

        # SERVER RELATED
        self.git_rev = getattr(config, 'git_rev', None)

        self.passwords = {}
        for k, v in config.passwords.iteritems():
            self.passwords[k.lower()] = v

        self.scripts = []
        for script in config.scripts:
            self.load_script(script)

        # INGAME TIME
        self.extra_elapsed_time = 0.0
        self.start_time = reactor.seconds()
        self.set_clock('12:00')


    def buildProtocol(self, addr):
        message = self.call_scripts('on_connection_attempt', addr)
        if message is False:
            return BanProtocol(message)
        return CubeWorldConnection(self, addr)


    def remove_item(self, chunk, index):
        try:
            items = self.chunk_items[chunk]
            ret = items.pop(index)
            self.items_changed = True
            return ret
        except KeyError:
            return None
        except IndexError:
            return None


    def drop_item(self, item_data, pos, lifetime=None):
        try:
            chunk_items = self.chunk_items[get_chunk(pos)]
            if len(chunk_items) < constants.MAX_ITEMS_PER_CHUNK:
                item = ChunkItemData()
                item.drop_time = 750 # ?
                item.scale = 0.1
                item.rotation = 185.0
                item.something3 = item.something5 = item.something6 = 0
                item.pos = pos
                item.item_data = item_data
                if lifetime is None:
                    item.despawn_time = reactor.seconds() + constants.MAX_ITEM_LIFETIME
                elif lifetime is not False:
                    item.despawn_time = reactor.seconds() + lifetime
                else:
                    item.despawn_time = None
                chunk_items.append(item)
                if item.despawn_time < self.next_items_autoremoval:
                    self.next_items_autoremoval = item.despawn_time
                self.items_changed = True
                return True
        except KeyError:
            pass
        except IndexError:
            pass
        return False


    def update(self):
        # secondly update check
        uxtime = int(reactor.seconds())
        update_seconds_delta = uxtime - self.last_secondly_check
        if update_seconds_delta == 0:
            self.ticks_since_last_second += 1
        else:
            self.last_secondly_check = uxtime
            if update_seconds_delta > 0:
                self.call_scripts('update')
                self.ticks_per_second = (self.ticks_per_second + (self.ticks_since_last_second / update_seconds_delta)) / 2
                self.ticks_since_last_second = 0
                if self.ticks_per_second < 25:
                    print '[WARNING] The amount of TPS is as low as %s' % self.ticks_per_second
            else:
                print '[WARNING] Seems like the reactor time went backwards! Ignoring.'
                update_seconds_delta = 0

        # entity updates
        for entity_id, entity in self.entities.iteritems():
            if entity.changed:
                entity.changed = False
                entity_packet.set_entity(entity, entity_id, entity.mask)
                entity.mask = 0
                self.broadcast_packet(entity_packet)
        self.broadcast_packet(update_finished_packet)

        # other updates
        update_packet = self.update_packet

        # item updates
        if uxtime >= self.next_items_autoremoval:
            self.next_items_autoremoval = self.last_secondly_check + 300
            for chunk, items in self.chunk_items.iteritems():
                new_chunk_items = []
                for item in items:
                    if not item.despawn_time or item.despawn_time > uxtime:
                        new_chunk_items.append(item)
                    else:
                        if item.despawn_time < self.next_items_autoremoval:
                            self.next_items_autoremoval = item.despawn_time
                        self.items_changed = True
                self.chunk_items[chunk] = new_chunk_items

        if self.items_changed:
            self.items_changed = False
            for chunk, items in self.chunk_items.iteritems():
                item_list = ChunkItems()
                item_list.chunk_x, item_list.chunk_y = chunk
                item_list.items = items
                update_packet.chunk_items.append(item_list)

        self.broadcast_packet(update_packet)
        update_packet.reset()

        if update_seconds_delta != 0:
            for connection in self.connections.values():
                if connection.time_last_packet > (uxtime - constants.CLIENT_RECV_TIMEOUT):
                    if connection.entity_data.changed:
                        connection.entity_data.changed = False
                        connection.do_anticheat_actions()
                    self.broadcast_time()
                else:
                    print '[WARNING] Connection timed out for Player %s (ID: %s)' % (connection.entity_data.name, connection.entity_id)
                    connection.kick('Connection timed out')


    def send_chat(self, value):
        packet = ServerChatMessage()
        packet.entity_id = 0
        packet.value = value
        self.broadcast_packet(packet)


    def broadcast_packet(self, packet):
        data = write_packet(packet)
        for connection in self.connections.values():
            connection.transport.write(data)


    def broadcast_time(self):
        time_packet.time = self.get_time()
        time_packet.day = self.get_day()
        self.broadcast_packet(time_packet)


    # line/string formatting options based on config

    def format(self, value):
        format_dict = {'server_name': self.config.server_name}
        return value % format_dict


    def format_lines(self, value):
        lines = []
        for line in value:
            lines.append(self.format(line))
        return lines


    # script methods

    def load_script(self, name):
        path = './scripts/%s.py' % name
        try:
            mod = imp.load_source(name, path)
        except IOError:
            return None
        script = mod.get_class()(self)
        print '[INFO] Loaded additional script "%s"' % name
        return script


    def call_scripts(self, name, *arg, **kw):
        return call_scripts(self.scripts, name, *arg, **kw)


    # data store methods

    def load_data(self, name, default = None):
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
        dt *= self.config.time_modifier * constants.NORMAL_TIME_SPEED
        return dt * 1000 + self.extra_elapsed_time


    def get_time(self):
        return int(self.get_elapsed_time() % constants.MAX_TIME)


    def get_day(self):
        return int(self.get_elapsed_time() / constants.MAX_TIME)


    def get_clock(self):
        return get_clock_string(self.get_time())



def main():
    # for py2exe
    if hasattr(sys, 'frozen'):
        path = os.path.dirname(
            unicode(sys.executable, sys.getfilesystemencoding()))
        sys.path.append(path)

    import config
    msg = '[INFO] Server is running on %r' % platform.system()
    revision = script.server.git_rev
    if revision:
        msg += ' with cuwo %s' % revision
    print msg
    reactor.listenTCP(constants.SERVER_PORT, CubeWorldServer(config))
    print '[INFO] cuwo is listining on port %s now.' % constants.SERVER_PORT
    if config.profile_file is None:
        reactor.run()
    else:
        import cProfile
        cProfile.run('reactor.run()', filename=config.profile_file)


if __name__ == '__main__':
    main()
