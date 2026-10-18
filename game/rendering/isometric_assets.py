"""Loads the isometric ground tile.

Loading is lazy (first call to get_grass_tile()) and cached, same
reasoning as game.rendering.assets: Surface.convert_alpha() requires an
active display mode, which isn't set up yet at import time.
"""

import glob
import os

import pygame

from game.paths import resource_path
from game.rendering.tile_geometry import TILE_WIDTH, TILE_HEIGHT

TILE_DIR = resource_path("assets/isometric tileset/separated images")
TILE_PATH = f"{TILE_DIR}/tile_022.png"
STONE_TILE_PATH = f"{TILE_DIR}/tile_063.png"

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


_all_tiles_cache = None


def get_all_tiles():
    """Every tile_*.png in the tileset folder, keyed by filename stem
    (e.g. "tile_022"). Used by the map editor's palette, which — unlike
    gameplay's fixed grass/stone choice — needs every tile art asset
    available to paint with. Discovered once and cached, same reasoning
    as _get_cached_tile."""
    global _all_tiles_cache
    if _all_tiles_cache is None:
        _all_tiles_cache = {
            os.path.splitext(os.path.basename(path))[0]: _get_cached_tile(path)
            for path in sorted(glob.glob(os.path.join(TILE_DIR, "tile_*.png")))
        }
    return _all_tiles_cache
