# Copyright (c) Julien Kross 2013.
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


from cuwo.vector import Vector3
from cuwo import constants
from cuwo import common

import collections
import math


# Returns set of locatables near a line e.g. for magic ranged attacks
def get_locatables_near_line(locatable_iter, x1, y1, z1, x2, y2, z2, lrud_dist=3):
    if not locatable_iter:
        return None
    lx = min(x1, x2)
    ly = min(y1, y2)
    lz = min(z1, z2)
    hx = max(x1, x2)
    hy = max(y1, y2)
    hz = max(z1, z2)
    max_distance = math.abs(max_distance)
    locatable_set = set()
    while True:
        try:
            ltv = next(locatable_iter)
            if not ltv:
                continue
            # Filter 1 (rectangular)
            if (ltv.x >= lx - lrud_dist) and (ltv.x <= hx + lrud_dist) and (ltv.y >= ly - lrud_dist) and (ltv.y <= hy + lrud_dist) and (ltv.z >= lz - lrud_dist) and (ltv.z <= hz + lrud_dist):
                    dst = ( ( (hx - lx) * (hy - ly) * (hz - lz) ) - ( (ltv.x - lx) * (ltv.y - ly) * (ltv.z - lz) ) ) / math.sqrt( math.hypot(hx - lx) + math.hypot(hy - ly) + math.hypot(hz - lz) )
                    # Filter 2 (point-line-distance)
                    if (dst <= lrud_dist):
                        locatable_set.add(ltv)
        except StopIteration:
            break
        except:
            continue
    return locatable_set

# Returns set of locatables in range
def get_locatables_in_range(locatable_iter, lx, ly, lz, max_distance=3):
    if not locatable_iter:
        return None
    max_distance = math.abs(max_distance)
    locatable_set = set()
    while True:
        try:
            ltv = next(locatable_iter)
            if not ltv:
                continue
            ltd = common.get_distance_3d(lx,
                                         ly,
                                         lz,
                                         ltv.x,
                                         ltv.y,
                                         ltv.z)
            if ( ltd <= max_distance ):
                locatable_set.add(ltv)
        except StopIteration:
            break
        except:
            continue
    return locatable_set

# Returns single closest locatable in range
def get_closest_locatable(locatable_iter, lx, ly, lz, max_distance=3):
    if not locatable_iter:
        return None
    max_distance = math.abs(max_distance)
    closest_dst = None
    closest_lct = None
    while True:
        try:
            ltv = next(locatable_iter)
            if not ltv:
                continue
            ltd = common.get_distance_3d(lx,
                                         ly,
                                         lz,
                                         ltv.x,
                                         ltv.y,
                                         ltv.z)
            if ( (not max_distance) or (ltd <= max_distance) ) and ( (not closest_dst) or (not closest_ent) or (ltd < closest_dst) ):
                closest_dst = ltd
                closest_lct = ltv
        except StopIteration:
            break
        except:
            continue
    return closest_lct

def get_scaled_xy(px, py, pscale):
    return list(math.floor( px / pscale ),
                math.floor( py / pscale ))

def get_scaled_min_max_xy(rx, ry, rdist, rscale):
    rx_center = rx / rscale
    ry_center = ry / rscale
    rdist_scaled = math.ceil( rdist / rscale )
    return list(math.floor( rx_center - rdist_scaled ),
                math.ceil(  rx_center + rdist_scaled ),
                math.floor( ry_center - rdist_scaled ),
                math.ceil(  ry_center + rdist_scaled ))


class Locatable(object):
    def __init__(self, x, y, z, id, obj=None):
        self.x = x
        self.y = y
        self.z = z
        self.id = id
        self.obj = obj

class Chunk(object):
    # chunk_pos = Vector2 of chunk position within sector
    def __init__(self, sector, cx, cy):
        self.sector = sector
        self.chunk_x = cx
        self.chunk_y = cy
        self.item_list = []
        self.locatables = {}

    def is_in_chunk(self, px, py):
        mmp = get_scaled_xy( px, py, constants.CHUNK_SCALE )
        if ( mmp[0] == self.chunk_x ) and ( mmp[1] == self.chunk_y ):
            return True
        return False

    # Returns single closest locatable
    def get_locatable(self, lx, ly, lz, max_distance=3):
        if len(self.locatables) < 1:
            return None
        return get_closest_locatable( self.locatables.itervalues(), lx, ly, lz, max_distance )

    # Returns set of locatables in range
    def get_locatables(self, lx, ly, lz, max_distance=3):
        if len(self.locatables) < 1:
            return None
        return get_locatables_in_range( self.locatables.itervalues(), lx, ly, lz, max_distance )

    def get_locatables_iter(self):
        return iter(self.locatables)

    def register_locatable(self, locatable):
        if not locatable:
            return
        self.locatables[locatable.id] = locatable

    def register(self, x, y, z, id, obj=None):
        lct = Locatable(x, y, z, id, obj)
        self.register_locatable(lct)
        return lct

    def unregister(self, id):
        return self.locatables.pop(id, None)


class Sector(object):
    def __init__(self, world, sx, sy):
        self.world = world
        self.sector_x = sx
        self.sector_y = sy

    def is_in_sector(self, px, py):
        mmp = get_scaled_xy( px, py, constants.SECTOR_SCALE )
        if ( mmp[0] == self.sector_x ) and ( mmp[1] == self.sector_y ):
            return True
        return False


class World(object):
    def __init__(self, server, name=None):
        self.server = server
        self.name = name
        self.chunks = {}
        self.sectors = {}
        self.locatables = {}

    def get_chunk_unscaled(self, cx, cy):
        cx = math.floor(cx)
        cy = math.floor(cy)
        chnk = None
        try:
            chnk = self.chunks[(cx, cy)]
        except KeyError:
            pass
        if not chnk:
            chnk = Chunk(self, cx, cy)
            self.chunks[(cx, cy)] = chnk
        return chnk

    # Get sector at sector position
    def get_sector_unscaled(self, sx, sy):
        sx = math.floor(sx)
        sy = math.floor(sy)
        secp = None
        try:
            secp = self.sectors[(sx, sy)]
        except:
            pass
        if not secp:
            secp = Sector(self, sx, sy)
            self.sectors[(sx, sy)] = secp
        return secp

    def get_chunk_scaled(self, px, py):
        return self.get_chunk_unscaled(math.floor( px / constants.CHUNK_SCALE),
                                       math.floor( py / constants.CHUNK_SCALE))

    # Get sector at x y position
    def get_sector_scaled(self, px, py):
        return self.get_sector_unscaled( math.floor( px / constants.SECTOR_SCALE),
                                         math.floor( py / constants.SECTOR_SCALE))

    # Get sector at chunk position
    def get_chunk_sector(self, cx, cy):
        return self.get_sector_unscaled( math.floor( (cx * constants.CHUNK_SCALE) / constants.SECTOR_SCALE),
                                         math.floor( (cy * constants.CHUNK_SCALE) / constants.SECTOR_SCALE))

    # 3 step targeting (World -> WorldSectors -> WorldChunks)
    # Returns locatables within max_distance
    def get_locatables(self, x, y, z, max_distance=3):
        locatables = set()
        # scale down to chunks
        rngs = get_scaled_min_max_xy( x, y, max_distance, constants.CHUNK_SCALE )
        # loop through chunks in within scaled max_distance
        for cx in range(rngs[0], rngs[1]):
            for cy in range(rngs[2], rngs[3]):
                # get closest locatables in current sector and add them to locatables set
                lcs = self.get_chunk_unscaled(cx, cy).get_locatables( x, y, z, max_distance )
                if not lcs:
                    continue
                locatables.update(lcs)
        return locatables

    # Returns single closest locatable within max_distance
    def get_locatable(self, x, y, z, max_distance=3):
        locatables = set()
        # scale down to chunks
        rngs = get_scaled_min_max_xy( x, y, max_distance, constants.CHUNK_SCALE )
        # loop through chunks in within scaled max_distance
        for cx in range(rngs[0], rngs[1]):
            for cy in range(rngs[2], rngs[3]):
                # get closest locatables in current chunk and add to locatables set
                lcs = self.get_chunk_unscaled(cx, cy).get_locatable( x, y, z, max_distance )
                if not lcs:
                    continue
                locatables.add(lcs)
        if len(locatables) < 1:
            return None
        return get_closest_locatable( iter(locatables), x, y, z, max_distance )

    def register(self, x, y, z, id, obj=None):
        lct = self.get_chunk_scaled(x, y).register(x, y, z, id, obj)
        self.locatables[id] = lct
        return lct

    def unregister(self, id):
        ret = self.locatables.pop(id, None)
        if not ret:
            return None
        return self.get_chunk_scaled(ret.x, ret.y).unregister(id)


    # unregisters from old chunk and registers in new
    # chunk only when moved from one chunk to another
    def move_locatable(self, locatable, new_x, new_y, new_z):
        locatable.z = new_z
        if (new_x != locatable.x) or (new_y != locatable.y):
            old_chunk_pos = get_scaled_xy( locatable.x, locatable.y, constants.CHUNK_SCALE )
            new_chunk_pos = get_scaled_xy( new_x,       new_y,       constants.CHUNK_SCALE )
            if (old_chunk_pos[0] == new_chunk_pos[0]) or (old_chunk_pos[1] == new_chunk_pos[1]):
                return
            self.unregister_locatable(locatable)
            locatable.x = new_x
            locatable.y = new_y
            self.register_locatable(locatable)
