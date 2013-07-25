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

from cuwo.loader import Loader
from cuwo.common import is_bit_set
from cuwo.vector import Vector3

FLAGS_1_HOSTILE = 0x20
POS_BIT = 0
ORIENT_BIT = 1
VEL_BIT = 2
ACCEL_BIT = 3
EXTRA_VEL_BIT = 4
LOOK_PITCH_BIT = 5
MODE_BIT = 9
CLASS_BIT = 21
MULTIPLIER_BIT = 30
LEVEL_BIT = 33
EQUIPMENT_BIT = 44
NAME_BIT = 45
SKILL_BIT = 46


class ItemUpgrade(Loader):
    def __init__(self):
        self.changed = False
        self.chunk = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.material = 0
        self.level = 0
        # change index set by server
        self.change_index = -1

    def read(self, reader):
        self.x = reader.read_int8()
        self.y = reader.read_int8()
        self.z = reader.read_int8()
        self.material = reader.read_int8()
        self.level = reader.read_uint32()
        # it could be changed means it has changed
        self.changed = True

    def write(self, writer):
        writer.write_int8(self.x)
        writer.write_int8(self.y)
        writer.write_int8(self.z)
        writer.write_int8(self.material)
        writer.write_uint32(self.level)


class ItemData(Loader):
    def __init__(self):
        self.changed = False
        self.chunk = None
        self.type = 0
        self.sub_type = 0
        self.modifier = 0
        self.minus_modifier = 0
        self.rarity = 0
        self.material = 0
        self.flags = 0
        self.level = 0
        self.items = []
        for _ in xrange(32):
            self.items.append(ItemUpgrade())
        self.upgrade_count = 0
        # change index set by server
        self.change_index = -1
        # double linked and set by the server


    def read(self, reader):
        self.type = reader.read_uint8()
        self.sub_type = reader.read_uint8()
        reader.skip(2)
        self.modifier = reader.read_uint32()
        self.minus_modifier = reader.read_uint32()
        self.rarity = reader.read_uint8()
        self.material = reader.read_uint8()
        self.flags = reader.read_uint8()
        reader.skip(1)
        self.level = reader.read_int16()
        reader.skip(2)
        self.items = []
        for _ in xrange(32):
            new_item = ItemUpgrade()
            new_item.read(reader)
            self.items.append(new_item)
        self.upgrade_count = reader.read_uint32()
        # it could be changed means it has changed
        self.changed = True

    def write(self, writer):
        writer.write_uint8(self.type)
        writer.write_uint8(self.sub_type)
        writer.pad(2)
        writer.write_uint32(self.modifier)
        writer.write_uint32(self.minus_modifier)
        writer.write_uint8(self.rarity)
        writer.write_uint8(self.material)
        writer.write_uint8(self.flags)
        writer.pad(1)
        writer.write_int16(self.level)
        writer.pad(2)
        for item in self.items:
            item.write(writer)
        writer.write_uint32(self.upgrade_count)


class AppearanceData(Loader):
    def __init__(self):
        self.changed = False
        self.not_used_1 = 0
        self.not_used_2 = 0
        self.hair_red = 255
        self.hair_green = 255
        self.hair_blue = 255
        self.movement_flags = 0
        self.entity_flags = 0
        self.scale = 1
        self.bounding_radius = 0
        self.bounding_height = 0
        self.head_model = 0
        self.hair_model = 0
        self.hand_model = 0
        self.foot_model = 0
        self.body_model = 0
        self.back_model = 0
        self.shoulder_model = 0
        self.wing_model = 0
        self.head_scale = 1
        self.body_scale = 1
        self.hand_scale = 1
        self.foot_scale = 1
        self.shoulder_scale = 1
        self.weapon_scale = 1
        self.back_scale = 1
        self.unknown = 1
        self.wing_scale = 1
        self.body_pitch = 0
        self.arm_pitch = 0
        self.arm_roll = 0
        self.arm_yaw = 0
        self.feet_pitch = 0
        self.wing_pitch = 0
        self.back_pitch = 0
        self.body_offset = Vector3(0, 0, 0)
        self.head_offset = Vector3(0, 0, 0)
        self.hand_offset = Vector3(0, 0, 0)
        self.foot_offset = Vector3(0, 0, 0)
        self.back_offset = Vector3(0, 0, 0)
        self.wing_offset = Vector3(0, 0, 0)
        # change index set by server
        self.change_index = -1

    def read(self, reader):
        self.not_used_1 = reader.read_uint8()
        self.not_used_2 = reader.read_uint8()
        self.hair_red = reader.read_uint8()
        self.hair_green = reader.read_uint8()
        self.hair_blue = reader.read_uint8()
        reader.skip(1)
        self.movement_flags = reader.read_uint8()
        self.entity_flags = reader.read_uint8()
        self.scale = reader.read_float()
        self.bounding_radius = reader.read_float()
        self.bounding_height = reader.read_float()
        self.head_model = reader.read_int16()
        self.hair_model = reader.read_int16()
        self.hand_model = reader.read_int16()
        self.foot_model = reader.read_int16()
        self.body_model = reader.read_int16()
        self.back_model = reader.read_int16()
        self.shoulder_model = reader.read_int16()
        self.wing_model = reader.read_int16()
        self.head_scale = reader.read_float()
        self.body_scale = reader.read_float()
        self.hand_scale = reader.read_float()
        self.foot_scale = reader.read_float()
        self.shoulder_scale = reader.read_float()
        self.weapon_scale = reader.read_float()
        self.back_scale = reader.read_float()
        self.unknown = reader.read_float()
        self.wing_scale = reader.read_float()
        self.body_pitch = reader.read_float()
        self.arm_pitch = reader.read_float()
        self.arm_roll = reader.read_float()
        self.arm_yaw = reader.read_float()
        self.feet_pitch = reader.read_float()
        self.wing_pitch = reader.read_float()
        self.back_pitch = reader.read_float()
        self.body_offset = reader.read_vec3()
        self.head_offset = reader.read_vec3()
        self.hand_offset = reader.read_vec3()
        self.foot_offset = reader.read_vec3()
        self.back_offset = reader.read_vec3()
        self.wing_offset = reader.read_vec3()
        # it could be changed means it has changed
        self.changed = True

    def write(self, writer):
        writer.write_uint8(self.not_used_1)
        writer.write_uint8(self.not_used_2)
        writer.write_uint8(self.hair_red)
        writer.write_uint8(self.hair_green)
        writer.write_uint8(self.hair_blue)
        writer.pad(1)
        writer.write_uint8(self.movement_flags)
        writer.write_uint8(self.entity_flags)
        writer.write_float(self.scale)
        writer.write_float(self.bounding_radius)
        writer.write_float(self.bounding_height)
        writer.write_int16(self.head_model)
        writer.write_int16(self.hair_model)
        writer.write_int16(self.hand_model)
        writer.write_int16(self.foot_model)
        writer.write_int16(self.body_model)
        writer.write_int16(self.back_model)
        writer.write_int16(self.shoulder_model)
        writer.write_int16(self.wing_model)
        writer.write_float(self.head_scale)
        writer.write_float(self.body_scale)
        writer.write_float(self.hand_scale)
        writer.write_float(self.foot_scale)
        writer.write_float(self.shoulder_scale)
        writer.write_float(self.weapon_scale)
        writer.write_float(self.back_scale)
        writer.write_float(self.unknown)
        writer.write_float(self.wing_scale)
        writer.write_float(self.body_pitch)
        writer.write_float(self.arm_pitch)
        writer.write_float(self.arm_roll)
        writer.write_float(self.arm_yaw)
        writer.write_float(self.feet_pitch)
        writer.write_float(self.wing_pitch)
        writer.write_float(self.back_pitch)
        writer.write_vec3(self.body_offset)
        writer.write_vec3(self.head_offset)
        writer.write_vec3(self.hand_offset)
        writer.write_vec3(self.foot_offset)
        writer.write_vec3(self.back_offset)
        writer.write_vec3(self.wing_offset)


class EntityData(Loader):
    def __init__(self):
        self.changed = False
        # double linked and set by the server
        self.chunk = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.body_roll = 0
        self.body_pitch = 0
        self.body_yaw = 0
        self.velocity = Vector3(0, 0, 0)
        self.accel = Vector3(0, 0, 0)
        self.extra_vel = Vector3(0, 0, 0)
        self.look_pitch = 0
        self.physics_flags = 0
        self.speed_flags = 0
        self.entity_type = 0
        self.current_mode = 0
        self.last_shoot_time = 0
        self.hit_counter = 0
        self.last_hit_time = 0
        self.appearance = AppearanceData()
        self.flags_1 = 0
        self.flags_2 = 0
        self.roll_time = 0
        self.stun_time = 0
        self.slowed_time = 0
        self.make_blue_time = 0
        self.speed_up_time = 0
        self.show_patch_time = 0
        self.class_type = 0
        self.specialization = 0
        self.charged_mp = 0
        self.not_used_1 = 0
        self.not_used_2 = 0
        self.not_used_3 = 0
        self.not_used_4 = 0
        self.not_used_5 = 0
        self.not_used_6 = 0
        self.ray_hit = Vector3(0, 0, 0)
        self.hp = 1
        self.mp = 0
        self.block_power = 0
        self.max_hp_multiplier = 1
        self.shoot_speed = 0
        self.damage_multiplier = 1
        self.armor_multiplier = 1
        self.resi_multiplier = 1
        self.not_used7 = 0
        self.not_used8 = 0
        self.level = 0
        self.current_xp = 0
        self.parent_owner = 0
        self.unknown_or_not_used1 = 0
        self.unknown_or_not_used2 = 0
        self.unknown_or_not_used3 = 0
        self.unknown_or_not_used4 = 0
        self.unknown_or_not_used5 = 0
        self.not_used11 = 0
        self.not_used12 = 0
        self.super_weird = 0
        self.not_used13 = 0
        self.not_used14 = 0
        self.not_used15 = 0
        self.not_used16 = 0
        self.not_used17 = 0
        self.not_used18 = 0
        self.not_used19 = 0
        self.not_used20 = 0
        self.not_used21 = 0
        self.not_used22 = 0
        self.item_data = ItemData()
        self.equipment = []
        for _ in xrange(13):
            self.equipment.append(ItemData())
        self.skills = []
        for _ in xrange(11):
            self.skills.append(0)
        self.ice_block_four = 0
        self.mana_cubes = 0
        self.name = ''
        # change index set by server
        self.change_index = -1

    def read(self, reader):
        self.x = reader.read_int64()
        self.y = reader.read_int64()
        self.z = reader.read_int64()
        self.body_roll = reader.read_float()
        self.body_pitch = reader.read_float()
        self.body_yaw = reader.read_float()
        self.velocity = reader.read_vec3()
        self.accel = reader.read_vec3()
        self.extra_vel = reader.read_vec3()
        self.look_pitch = reader.read_float()
        self.physics_flags = reader.read_uint32()
        self.speed_flags = reader.read_uint8()
        reader.skip(3)
        self.entity_type = reader.read_uint32()
        self.current_mode = reader.read_uint8()
        reader.skip(3)
        self.last_shoot_time = reader.read_uint32()
        self.hit_counter = reader.read_uint32()
        self.last_hit_time = reader.read_uint32()
        self.appearance = AppearanceData()
        self.appearance.read(reader)
        self.flags_1 = reader.read_uint8()
        self.flags_2 = reader.read_uint8()
        reader.skip(2)
        self.roll_time = reader.read_uint32()
        self.stun_time = reader.read_int32()
        self.slowed_time = reader.read_uint32()
        self.make_blue_time = reader.read_uint32()
        self.speed_up_time = reader.read_uint32()
        self.show_patch_time = reader.read_float()
        self.class_type = reader.read_uint8()
        self.specialization = reader.read_uint8()
        reader.skip(2)
        self.charged_mp = reader.read_float()
        self.not_used_1 = reader.read_uint32()
        self.not_used_2 = reader.read_uint32()
        self.not_used_3 = reader.read_uint32()
        self.not_used_4 = reader.read_uint32()
        self.not_used_5 = reader.read_uint32()
        self.not_used_6 = reader.read_uint32()
        self.ray_hit = reader.read_vec3()
        self.hp = reader.read_float()
        self.mp = reader.read_float()
        self.block_power = reader.read_float()
        self.max_hp_multiplier = reader.read_float()
        self.shoot_speed = reader.read_float()
        self.damage_multiplier = reader.read_float()
        self.armor_multiplier = reader.read_float()
        self.resi_multiplier = reader.read_float()
        self.not_used7 = reader.read_uint8()
        self.not_used8 = reader.read_uint8()
        reader.skip(2)
        self.level = reader.read_uint32()
        self.current_xp = reader.read_uint32()
        self.parent_owner = reader.read_uint64()
        self.unknown_or_not_used1 = reader.read_uint32()
        self.unknown_or_not_used2 = reader.read_uint32()
        self.unknown_or_not_used3 = reader.read_uint8()
        reader.skip(3)
        self.unknown_or_not_used4 = reader.read_uint32()
        self.unknown_or_not_used5 = reader.read_uint32()
        self.not_used11 = reader.read_uint32()
        self.not_used12 = reader.read_uint32()
        self.super_weird = reader.read_uint32()
        self.not_used13 = reader.read_uint32()
        self.not_used14 = reader.read_uint32()
        self.not_used15 = reader.read_uint32()
        self.not_used16 = reader.read_uint32()
        self.not_used17 = reader.read_uint32()
        self.not_used18 = reader.read_uint32()
        self.not_used19 = reader.read_uint8()
        reader.skip(3)
        self.not_used20 = reader.read_uint32()
        self.not_used21 = reader.read_uint32()
        self.not_used22 = reader.read_uint32()
        self.item_data = ItemData()
        self.item_data.read(reader)
        self.equipment = []
        for _ in xrange(13):
            new_item = ItemData()
            new_item.read(reader)
            self.equipment.append(new_item)
        self.skills = []
        for _ in xrange(11):
            self.skills.append(reader.read_uint32())
        self.mana_cubes = reader.read_uint32()
        self.name = reader.read_ascii(16)
        # it could be changed means it has changed
        self.changed = True

    def write(self, writer):
        writer.write_int64(self.x)
        writer.write_int64(self.y)
        writer.write_int64(self.z)
        writer.write_float(self.body_roll)
        writer.write_float(self.body_pitch)
        writer.write_float(self.body_yaw)
        writer.write_vec3(self.velocity)
        writer.write_vec3(self.accel)
        writer.write_vec3(self.extra_vel)
        writer.write_float(self.look_pitch)
        writer.write_uint32(self.physics_flags)
        writer.write_uint8(self.speed_flags)
        writer.pad(3)
        writer.write_uint32(self.entity_type)
        writer.write_uint8(self.current_mode)
        writer.pad(3)
        writer.write_uint32(self.last_shoot_time)
        writer.write_uint32(self.hit_counter)
        writer.write_uint32(self.last_hit_time)
        self.appearance.write(writer)
        writer.write_uint8(self.flags_1)
        writer.write_uint8(self.flags_2)
        writer.pad(2)
        writer.write_uint32(self.roll_time)
        writer.write_int32(self.stun_time)
        writer.write_uint32(self.slowed_time)
        writer.write_uint32(self.make_blue_time)
        writer.write_uint32(self.speed_up_time)
        writer.write_float(self.show_patch_time)
        writer.write_uint8(self.class_type)
        writer.write_uint8(self.specialization)
        writer.pad(2)
        writer.write_float(self.charged_mp)
        writer.write_uint32(self.not_used_1)
        writer.write_uint32(self.not_used_2)
        writer.write_uint32(self.not_used_3)
        writer.write_uint32(self.not_used_4)
        writer.write_uint32(self.not_used_5)
        writer.write_uint32(self.not_used_6)
        writer.write_vec3(self.ray_hit)
        writer.write_float(self.hp)
        writer.write_float(self.mp)
        writer.write_float(self.block_power)
        writer.write_float(self.max_hp_multiplier)
        writer.write_float(self.shoot_speed)
        writer.write_float(self.damage_multiplier)
        writer.write_float(self.armor_multiplier)
        writer.write_float(self.resi_multiplier)
        writer.write_uint8(self.not_used7)
        writer.write_uint8(self.not_used8)
        writer.pad(2)
        writer.write_uint32(self.level)
        writer.write_uint32(self.current_xp)
        writer.write_uint64(self.parent_owner)
        writer.write_uint32(self.unknown_or_not_used1)
        writer.write_uint32(self.unknown_or_not_used2)
        writer.write_uint8(self.unknown_or_not_used3)
        writer.pad(3)
        writer.write_uint32(self.unknown_or_not_used4)
        writer.write_uint32(self.unknown_or_not_used5)
        writer.write_uint32(self.not_used11)
        writer.write_uint32(self.not_used12)
        writer.write_uint32(self.super_weird)
        writer.write_uint32(self.not_used13)
        writer.write_uint32(self.not_used14)
        writer.write_uint32(self.not_used15)
        writer.write_uint32(self.not_used16)
        writer.write_uint32(self.not_used17)
        writer.write_uint32(self.not_used18)
        writer.write_uint8(self.not_used19)
        writer.pad(3)
        writer.write_uint32(self.not_used20)
        writer.write_uint32(self.not_used21)
        writer.write_uint32(self.not_used22)
        self.item_data.write(writer)
        for item in self.equipment:
            item.write(writer)
        for item in self.skills:
            writer.write_uint32(item)
        writer.write_uint32(self.mana_cubes)
        writer.write_ascii(self.name, 16)


def is_pos_set(mask):
    return is_bit_set(mask, POS_BIT)


def is_orient_set(mask):
    return is_bit_set(mask, ORIENT_BIT)


def is_vel_set(mask):
    return is_bit_set(mask, VEL_BIT)


def is_accel_set(mask):
    return is_bit_set(mask, ACCEL_BIT)


def is_extra_vel_set(mask):
    return is_bit_set(mask, EXTRA_VEL_BIT)


def is_look_pitch_set(mask):
    return is_bit_set(mask, LOOK_PITCH_BIT)


def is_mode_set(mask):
    return is_bit_set(mask, MODE_BIT)


def is_class_set(mask):
    return is_bit_set(mask, CLASS_BIT)


def is_multiplier_set(mask):
    return is_bit_set(mask, MULTIPLIER_BIT)


def is_level_set(mask):
    return is_bit_set(mask, LEVEL_BIT)


def is_equipment_set(mask):
    return is_bit_set(mask, EQUIPMENT_BIT)


def is_name_set(mask):
    return is_bit_set(mask, NAME_BIT)


def is_skill_set(mask):
    return is_bit_set(mask, SKILL_BIT)


def read_masked_data(entity, reader):
    mask = reader.read_uint64()
    if is_pos_set(mask):
        entity.x = reader.read_int64()
        entity.y = reader.read_int64()
        entity.z = reader.read_int64()
    if is_orient_set(mask):
        entity.body_roll = reader.read_float()
        entity.body_pitch = reader.read_float()
        entity.body_yaw = reader.read_float()
    if is_vel_set(mask):
        entity.velocity = reader.read_vec3()
    if is_accel_set(mask):
        entity.accel = reader.read_vec3()
    if is_extra_vel_set(mask):
        entity.extra_vel = reader.read_vec3()
    if is_look_pitch_set(mask):
        entity.look_pitch = reader.read_float()
    if is_bit_set(mask, 6):
        entity.physics_flags = reader.read_uint32()
    if is_bit_set(mask, 7):
        entity.speed_flags = reader.read_uint8()
    if is_bit_set(mask, 8):
        entity.entity_type = reader.read_uint32()
    if is_mode_set(mask):
        entity.current_mode = reader.read_uint8()
    if is_bit_set(mask, 10):
        entity.last_shoot_time = reader.read_uint32()
    if is_bit_set(mask, 11):
        entity.hit_counter = reader.read_uint32()
    if is_bit_set(mask, 12):
        entity.last_hit_time = reader.read_uint32()
    if is_bit_set(mask, 13):
        entity.appearance.read(reader)
    if is_bit_set(mask, 14):
        entity.flags_1 = reader.read_uint8()
        entity.flags_2 = reader.read_uint8()
    if is_bit_set(mask, 15):
        entity.roll_time = reader.read_uint32()
    if is_bit_set(mask, 16):
        entity.stun_time = reader.read_int32()
    if is_bit_set(mask, 17):
        entity.slowed_time = reader.read_uint32()
    if is_bit_set(mask, 18):
        entity.make_blue_time = reader.read_uint32()
    if is_bit_set(mask, 19):
        entity.speed_up_time = reader.read_uint32()
    if is_bit_set(mask, 20):
        entity.show_patch_time = reader.read_float()
    if is_class_set(mask):
        entity.class_type = reader.read_uint8()
    if is_bit_set(mask, 22):
        entity.specialization = reader.read_uint8()
    if is_bit_set(mask, 23):
        entity.charged_mp = reader.read_float()
    if is_bit_set(mask, 24):
        entity.not_used_1 = reader.read_uint32()
        entity.not_used_2 = reader.read_uint32()
        entity.not_used_3 = reader.read_uint32()
    if is_bit_set(mask, 25):
        entity.not_used_4 = reader.read_uint32()
        entity.not_used_5 = reader.read_uint32()
        entity.not_used_6 = reader.read_uint32()
    if is_bit_set(mask, 26):
        entity.ray_hit = reader.read_vec3()
    if is_bit_set(mask, 27):
        entity.hp = reader.read_float()
    if is_bit_set(mask, 28):
        entity.mp = reader.read_float()
    if is_bit_set(mask, 29):
        entity.block_power = reader.read_float()
    if is_multiplier_set(mask):
        entity.max_hp_multiplier = reader.read_float()
        entity.shoot_speed = reader.read_float()
        entity.damage_multiplier = reader.read_float()
        entity.armor_multiplier = reader.read_float()
        entity.resi_multiplier = reader.read_float()
    if is_bit_set(mask, 31):
        entity.not_used7 = reader.read_uint8()
    if is_bit_set(mask, 32):
        entity.not_used8 = reader.read_uint8()
    if is_level_set(mask):
        entity.level = reader.read_uint32()
    if is_bit_set(mask, 34):
        entity.current_xp = reader.read_uint32()
    if is_bit_set(mask, 35):
        entity.parent_owner = reader.read_uint64()
    if is_bit_set(mask, 36):
        entity.unknown_or_not_used1 = reader.read_uint32()
        entity.unknown_or_not_used2 = reader.read_uint32()
    if is_bit_set(mask, 37):
        entity.unknown_or_not_used3 = reader.read_uint8()
    if is_bit_set(mask, 38):
        entity.unknown_or_not_used4 = reader.read_uint32()
    if is_bit_set(mask, 39):
        entity.unknown_or_not_used5 = reader.read_uint32()
        entity.not_used11 = reader.read_uint32()
        entity.not_used12 = reader.read_uint32()
    if is_bit_set(mask, 40):
        entity.not_used13 = reader.read_uint32()
        entity.not_used14 = reader.read_uint32()
        entity.not_used15 = reader.read_uint32()
        entity.not_used16 = reader.read_uint32()
        entity.not_used17 = reader.read_uint32()
        entity.not_used18 = reader.read_uint32()
    if is_bit_set(mask, 41):
        entity.not_used20 = reader.read_uint32()
        entity.not_used21 = reader.read_uint32()
        entity.not_used22 = reader.read_uint32()
    if is_bit_set(mask, 42):
        entity.not_used19 = reader.read_uint8()
    if is_bit_set(mask, 43):
        entity.item_data.read(reader)
    if is_equipment_set(mask):
        for item in entity.equipment:
            item.read(reader)
    if is_name_set(mask):
        entity.name = reader.read_ascii(16)
    if is_skill_set(mask):
        entity.skills = []
        for _ in xrange(11):
            entity.skills.append(reader.read_uint32())
    if is_bit_set(mask, 47):
        entity.mana_cubes = reader.read_uint32()
    entity.changed = True
    return mask


def get_masked_size(mask):
    size = 0
    if is_pos_set(mask):
        size += 24
    if is_orient_set(mask):
        size += 12
    if is_vel_set(mask):
        size += 12
    if is_accel_set(mask):
        size += 12
    if is_extra_vel_set(mask):
        size += 12
    if is_look_pitch_set(mask):
        size += 4
    if is_bit_set(mask, 6):
        size += 4
    if is_bit_set(mask, 7):
        size += 1
    if is_bit_set(mask, 8):
        size += 4
    if is_mode_set(mask):
        size += 1
    if is_bit_set(mask, 10):
        size += 4
    if is_bit_set(mask, 11):
        size += 4
    if is_bit_set(mask, 12):
        size += 4
    if is_bit_set(mask, 13):
        size += 172
    if is_bit_set(mask, 14):
        size += 2
    if is_bit_set(mask, 15):
        size += 4
    if is_bit_set(mask, 16):
        size += 4
    if is_bit_set(mask, 17):
        size += 4
    if is_bit_set(mask, 18):
        size += 4
    if is_bit_set(mask, 19):
        size += 4
    if is_bit_set(mask, 20):
        size += 4
    if is_class_set(mask):
        size += 1
    if is_bit_set(mask, 22):
        size += 1
    if is_bit_set(mask, 23):
        size += 4
    if is_bit_set(mask, 24):
        size += 12
    if is_bit_set(mask, 25):
        size += 12
    if is_bit_set(mask, 26):
        size += 12
    if is_bit_set(mask, 27):
        size += 4
    if is_bit_set(mask, 28):
        size += 4
    if is_bit_set(mask, 29):
        size += 4
    if is_multiplier_set(mask):
        size += 20
    if is_bit_set(mask, 31):
        size += 1
    if is_bit_set(mask, 32):
        size += 1
    if is_level_set(mask):
        size += 4
    if is_bit_set(mask, 34):
        size += 4
    if is_bit_set(mask, 35):
        size += 8
    if is_bit_set(mask, 36):
        size += 8
    if is_bit_set(mask, 37):
        size += 1
    if is_bit_set(mask, 38):
        size += 4
    if is_bit_set(mask, 39):
        size += 12
    if is_bit_set(mask, 40):
        size += 24
    if is_bit_set(mask, 41):
        size += 12
    if is_bit_set(mask, 42):
        size += 1
    if is_bit_set(mask, 43):
        size += 280
    if is_equipment_set(mask):
        size += 3640
    if is_name_set(mask):
        size += 16
    if is_skill_set(mask):
        size += 44
    if is_bit_set(mask, 47):
        size += 4
    return size


def write_masked_data(entity, writer, mask=None):
    if mask is None:
        mask = 0x0000FFFFFFFFFFFF
    if mask <= 0:
        return
    writer.write_uint64(mask)
    if is_pos_set(mask):
        writer.write_int64(entity.x)
        writer.write_int64(entity.y)
        writer.write_int64(entity.z)
    if is_orient_set(mask):
        writer.write_float(entity.body_roll)
        writer.write_float(entity.body_pitch)
        writer.write_float(entity.body_yaw)
    if is_vel_set(mask):
        writer.write_vec3(entity.velocity)
    if is_accel_set(mask):
        writer.write_vec3(entity.accel)
    if is_extra_vel_set(mask):
        writer.write_vec3(entity.extra_vel)
    if is_look_pitch_set(mask):
        writer.write_float(entity.look_pitch)
    if is_bit_set(mask, 6):
        writer.write_uint32(entity.physics_flags)
    if is_bit_set(mask, 7):
        writer.write_uint8(entity.speed_flags)
    if is_bit_set(mask, 8):
        writer.write_uint32(entity.entity_type)
    if is_mode_set(mask):
        writer.write_uint8(entity.current_mode)
    if is_bit_set(mask, 10):
        writer.write_uint32(entity.last_shoot_time)
    if is_bit_set(mask, 11):
        writer.write_uint32(entity.hit_counter)
    if is_bit_set(mask, 12):
        writer.write_uint32(entity.last_hit_time)
    if is_bit_set(mask, 13):
        entity.appearance.write(writer)
    if is_bit_set(mask, 14):
        writer.write_uint8(entity.flags_1)
        writer.write_uint8(entity.flags_2)
    if is_bit_set(mask, 15):
        writer.write_uint32(entity.roll_time)
    if is_bit_set(mask, 16):
        writer.write_int32(entity.stun_time)
    if is_bit_set(mask, 17):
        writer.write_uint32(entity.slowed_time)
    if is_bit_set(mask, 18):
        writer.write_uint32(entity.make_blue_time)
    if is_bit_set(mask, 19):
        writer.write_uint32(entity.speed_up_time)
    if is_bit_set(mask, 20):
        writer.write_float(entity.show_patch_time)
    if is_class_set(mask):
        writer.write_uint8(entity.class_type)
    if is_bit_set(mask, 22):
        writer.write_uint8(entity.specialization)
    if is_bit_set(mask, 23):
        writer.write_float(entity.charged_mp)
    if is_bit_set(mask, 24):
        writer.write_uint32(entity.not_used_1)
        writer.write_uint32(entity.not_used_2)
        writer.write_uint32(entity.not_used_3)
    if is_bit_set(mask, 25):
        writer.write_uint32(entity.not_used_4)
        writer.write_uint32(entity.not_used_5)
        writer.write_uint32(entity.not_used_6)
    if is_bit_set(mask, 26):
        writer.write_vec3(entity.ray_hit)
    if is_bit_set(mask, 27):
        writer.write_float(entity.hp)
    if is_bit_set(mask, 28):
        writer.write_float(entity.mp)
    if is_bit_set(mask, 29):
        writer.write_float(entity.block_power)
    if is_multiplier_set(mask):
        writer.write_float(entity.max_hp_multiplier)
        writer.write_float(entity.shoot_speed)
        writer.write_float(entity.damage_multiplier)
        writer.write_float(entity.armor_multiplier)
        writer.write_float(entity.resi_multiplier)
    if is_bit_set(mask, 31):
        writer.write_uint8(entity.not_used7)
    if is_bit_set(mask, 32):
        writer.write_uint8(entity.not_used8)
    if is_level_set(mask):
        writer.write_uint32(entity.level)
    if is_bit_set(mask, 34):
        writer.write_uint32(entity.current_xp)
    if is_bit_set(mask, 35):
        writer.write_uint64(entity.parent_owner)
    if is_bit_set(mask, 36):
        writer.write_uint32(entity.unknown_or_not_used1)
        writer.write_uint32(entity.unknown_or_not_used2)
    if is_bit_set(mask, 37):
        writer.write_uint8(entity.unknown_or_not_used3)
    if is_bit_set(mask, 38):
        writer.write_uint32(entity.unknown_or_not_used4)
    if is_bit_set(mask, 39):
        writer.write_uint32(entity.unknown_or_not_used5)
        writer.write_uint32(entity.not_used11)
        writer.write_uint32(entity.not_used12)
    if is_bit_set(mask, 40):
        writer.write_uint32(entity.not_used13)
        writer.write_uint32(entity.not_used14)
        writer.write_uint32(entity.not_used15)
        writer.write_uint32(entity.not_used16)
        writer.write_uint32(entity.not_used17)
        writer.write_uint32(entity.not_used18)
    if is_bit_set(mask, 41):
        writer.write_uint32(entity.not_used20)
        writer.write_uint32(entity.not_used21)
        writer.write_uint32(entity.not_used22)
    if is_bit_set(mask, 42):
        writer.write_uint8(entity.not_used19)
    if is_bit_set(mask, 43):
        entity.item_data.write(writer)
    if is_equipment_set(mask):
        for item in entity.equipment:
            item.write(writer)
    if is_name_set(mask):
        writer.write_ascii(entity.name, 16)
    if is_skill_set(mask):
        for item in entity.skills:
            writer.write_uint32(item)
    if is_bit_set(mask, 47):
        writer.write_uint32(entity.mana_cubes)
