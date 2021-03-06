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
Entity data read/write

NOTE: This file is automatically generated. Do not modify.
"""

from cuwo.loader import Loader
from cuwo.common import is_bit_set


class ItemUpgrade(Loader):
    def read(self, reader):
        self.x = reader.read_int8()
        self.y = reader.read_int8()
        self.z = reader.read_int8()
        self.material = reader.read_int8()
        self.level = reader.read_uint32()

    def write(self, writer):
        writer.write_int8(self.x)
        writer.write_int8(self.y)
        writer.write_int8(self.z)
        writer.write_int8(self.material)
        writer.write_uint32(self.level)


class ItemData(Loader):
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


FLAGS_1_HOSTILE = 0x20
POS_BIT = 0
ORIENT_BIT = 1
VEL_BIT = 2
ACCEL_BIT = 3
EXTRA_VEL_BIT = 4
LOOK_PITCH_BIT = 5
MODE_BIT = 9
APPEARANCE_BIT = 13
FLAGS_BIT = 14
CLASS_BIT = 21
CHARGED_MP_BIT = 23
MULTIPLIER_BIT = 30
LEVEL_BIT = 33
CONSUMABLE_BIT = 43
EQUIPMENT_BIT = 44
NAME_BIT = 45
SKILL_BIT = 46


class EntityData(Loader):
    mask = 0

    def read(self, reader):
        self.pos = reader.read_qvec3()
        self.body_roll = reader.read_float()
        self.body_pitch = reader.read_float()
        self.body_yaw = reader.read_float()
        self.velocity = reader.read_vec3()
        self.accel = reader.read_vec3()
        self.extra_vel = reader.read_vec3()
        self.look_pitch = reader.read_float()
        self.physics_flags = reader.read_uint32()
        self.hostile_type = reader.read_uint8()
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
        self.spawn_pos = reader.read_qvec3()
        self.not_used19 = reader.read_uint8()
        reader.skip(3)
        self.not_used20 = reader.read_uint32()
        self.not_used21 = reader.read_uint32()
        self.not_used22 = reader.read_uint32()
        self.consumable = ItemData()
        self.consumable.read(reader)
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

    def write(self, writer):
        writer.write_qvec3(self.pos)
        writer.write_float(self.body_roll)
        writer.write_float(self.body_pitch)
        writer.write_float(self.body_yaw)
        writer.write_vec3(self.velocity)
        writer.write_vec3(self.accel)
        writer.write_vec3(self.extra_vel)
        writer.write_float(self.look_pitch)
        writer.write_uint32(self.physics_flags)
        writer.write_uint8(self.hostile_type)
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
        writer.write_qvec3(self.spawn_pos)
        writer.write_uint8(self.not_used19)
        writer.pad(3)
        writer.write_uint32(self.not_used20)
        writer.write_uint32(self.not_used21)
        writer.write_uint32(self.not_used22)
        self.consumable.write(writer)
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


def is_appearance_set(mask):
    return is_bit_set(mask, APPEARANCE_BIT)


def is_flags_set(mask):
    return is_bit_set(mask, FLAGS_BIT)


def is_class_set(mask):
    return is_bit_set(mask, CLASS_BIT)


def is_charged_mp_set(mask):
    return is_bit_set(mask, CHARGED_MP_BIT)


def is_multiplier_set(mask):
    return is_bit_set(mask, MULTIPLIER_BIT)


def is_level_set(mask):
    return is_bit_set(mask, LEVEL_BIT)


def is_consumable_set(mask):
    return is_bit_set(mask, CONSUMABLE_BIT)


def is_equipment_set(mask):
    return is_bit_set(mask, EQUIPMENT_BIT)


def is_name_set(mask):
    return is_bit_set(mask, NAME_BIT)


def is_skill_set(mask):
    return is_bit_set(mask, SKILL_BIT)


def read_masked_data(entity, reader):
    mask = reader.read_uint64()
    if is_pos_set(mask):
        entity.pos = reader.read_qvec3()
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
        entity.hostile_type = reader.read_uint8()
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
    if is_appearance_set(mask):
        entity.appearance.read(reader)
    if is_flags_set(mask):
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
    if is_charged_mp_set(mask):
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
        entity.spawn_pos = reader.read_qvec3()
    if is_bit_set(mask, 41):
        entity.not_used20 = reader.read_uint32()
        entity.not_used21 = reader.read_uint32()
        entity.not_used22 = reader.read_uint32()
    if is_bit_set(mask, 42):
        entity.not_used19 = reader.read_uint8()
    if is_consumable_set(mask):
        entity.consumable.read(reader)
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
    if is_appearance_set(mask):
        size += 172
    if is_flags_set(mask):
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
    if is_charged_mp_set(mask):
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
    if is_consumable_set(mask):
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

    writer.write_uint64(mask)
    if is_pos_set(mask):
        writer.write_qvec3(entity.pos)
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
        writer.write_uint8(entity.hostile_type)
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
    if is_appearance_set(mask):
        entity.appearance.write(writer)
    if is_flags_set(mask):
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
    if is_charged_mp_set(mask):
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
        writer.write_qvec3(entity.spawn_pos)
    if is_bit_set(mask, 41):
        writer.write_uint32(entity.not_used20)
        writer.write_uint32(entity.not_used21)
        writer.write_uint32(entity.not_used22)
    if is_bit_set(mask, 42):
        writer.write_uint8(entity.not_used19)
    if is_consumable_set(mask):
        entity.consumable.write(writer)
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

