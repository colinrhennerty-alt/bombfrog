"""Loads the isometric ground tile.

Loading is lazy (first call to get_grass_tile()) and cached, same
reasoning as game.rendering.assets: Surface.convert_alpha() requires an
active display mode, which isn't set up yet at import time.
"""

import pygame

TILE_PATH = "assets/isometric tileset/separated images/tile_022.png"
TILE_WIDTH = 64
TILE_HEIGHT = 64

_grass_tile_cache = None


def _load_grass_tile():
    tile = pygame.image.load(TILE_PATH).convert_alpha()
    return pygame.transform.scale(tile, (TILE_WIDTH, TILE_HEIGHT))


def get_grass_tile():
    global _grass_tile_cache
    if _grass_tile_cache is None:
        _grass_tile_cache = _load_grass_tile()
    return _grass_tile_cache
