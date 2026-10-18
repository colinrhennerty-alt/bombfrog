"""Loads the isometric ground tiles (Gridwright floors).

Loading is lazy (first call to get_grass_tile()) and cached, same
reasoning as game.rendering.assets: Surface.convert_alpha() requires an
active display mode, which isn't set up yet at import time.
"""

import glob
import os

import pygame

from game.paths import resource_path
from game.rendering.tile_geometry import TILE_WIDTH, TILE_HEIGHT

TILE_DIR = resource_path("assets/gridwright/floors")
TILE_PATH = f"{TILE_DIR}/floor_grass_01.png"
STONE_TILE_PATH = f"{TILE_DIR}/floor_stone_01.png"

_tile_cache = {}


def _load_tile(path):
    tile = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(tile, (TILE_WIDTH, TILE_HEIGHT))


def _get_cached_tile(path):
    if path not in _tile_cache:
        _tile_cache[path] = _load_tile(path)
    return _tile_cache[path]


def get_grass_tile():
    return _get_cached_tile(TILE_PATH)


def get_stone_tile():
    return _get_cached_tile(STONE_TILE_PATH)


def get_tile(tile_id):
    """One tile by id (e.g. "floor_grass_01"), for drawing a generated or
    authored ground map without loading the editor's whole palette."""
    return _get_cached_tile(f"{TILE_DIR}/{tile_id}.png")


_all_tiles_cache = None


def get_all_tiles():
    """Every floor_*.png in the tileset folder, keyed by filename stem
    (e.g. "floor_grass_01"). Used by the map editor's palette, which — unlike
    gameplay's fixed grass/stone choice — needs every tile art asset
    available to paint with. Discovered once and cached, same reasoning
    as _get_cached_tile."""
    global _all_tiles_cache
    if _all_tiles_cache is None:
        _all_tiles_cache = {
            os.path.splitext(os.path.basename(path))[0]: _get_cached_tile(path)
            for path in sorted(glob.glob(os.path.join(TILE_DIR, "floor_*.png")))
        }
    return _all_tiles_cache
