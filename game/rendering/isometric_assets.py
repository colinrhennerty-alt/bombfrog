"""Loads the isometric ground tile.

Loading is lazy (first call to get_grass_tile()) and cached, same
reasoning as game.rendering.assets: Surface.convert_alpha() requires an
active display mode, which isn't set up yet at import time.
"""

import pygame

TILE_PATH = "assets/isometric tileset/separated images/tile_022.png"
STONE_TILE_PATH = "assets/isometric tileset/separated images/tile_063.png"
TILE_WIDTH = 64
TILE_HEIGHT = 64

# The source art is a 32x32 sprite of a diamond-topped block: the diamond
# face itself only spans rows ~4-28 (24px, measured from the sprite's alpha
# channel), not the full 32px height — the rest is the block's side "skirt".
# Grid spacing must be based on the diamond's own footprint, not the full
# sprite size, or adjacent tiles cover too much of each other (or too
# little). 24/32 of TILE_WIDTH, scaled the same way the sprite is.
TILE_FOOTPRINT_HEIGHT = TILE_WIDTH * 24 / 32

_grass_tile_cache = None
_stone_tile_cache = None


def _load_tile(path):
    tile = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(tile, (TILE_WIDTH, TILE_HEIGHT))


def get_grass_tile():
    global _grass_tile_cache
    if _grass_tile_cache is None:
        _grass_tile_cache = _load_tile(TILE_PATH)
    return _grass_tile_cache


def get_stone_tile():
    global _stone_tile_cache
    if _stone_tile_cache is None:
        _stone_tile_cache = _load_tile(STONE_TILE_PATH)
    return _stone_tile_cache
