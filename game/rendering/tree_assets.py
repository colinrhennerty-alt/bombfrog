"""Loads the Gridwright tree sprites and their shadow sprites.

Each image comes with an offset: where its top-left sits relative to the
tree's trunk base (game.simulation.trees.Tree x/y), in screen px. The pack's
isometric.json anchors every sprite at its ground cell's back corner; the
trunk stands at the cell's center, half a ground diamond below that.

Loading is lazy and cached, same reasoning as game.rendering.assets:
Surface.convert_alpha() requires an active display mode.
"""

import json

import pygame

from game.config import TREE_SCALE
from game.paths import resource_path

PACK_DIR = resource_path("assets/gridwright")
TRUNK_BELOW_ANCHOR = 8  # art px: half of the pack's 16 px ground diamond
# The pack's README: solid shadow sprites, drawn at about 35% opacity.
SHADOW_ALPHA = 90
FADED_ALPHA = 128

_sprites_meta = None
_cache = {}


def _meta(name):
    global _sprites_meta
    if _sprites_meta is None:
        with open(f"{PACK_DIR}/isometric.json", encoding="utf-8") as f:
            _sprites_meta = json.load(f)["sprites"]
    return _sprites_meta[name]


def _load(name, folder, alpha):
    key = (name, alpha)
    if key not in _cache:
        image = pygame.image.load(f"{PACK_DIR}/{folder}/{name}.png").convert_alpha()
        image = pygame.transform.scale(image, (image.get_width() * TREE_SCALE, image.get_height() * TREE_SCALE))
        if alpha is not None:
            image.set_alpha(alpha)
        anchor_x, anchor_y = _meta(name)["anchor"]
        offset = (-anchor_x * TREE_SCALE, -(anchor_y + TRUNK_BELOW_ANCHOR) * TREE_SCALE)
        _cache[key] = (image, offset)
    return _cache[key]


def get_tree_sprite(kind, faded=False):
    """(surface, offset) for a tree; faded is the see-through copy drawn
    when the tree stands in front of the frog."""
    return _load(kind, "trees", FADED_ALPHA if faded else None)


def get_tree_shadow(kind):
    """(surface, offset) for a tree's shadow sprite (shared between trees
    of the same shape, e.g. every large oak)."""
    return _load(_meta(kind)["shadow"], "shadows", SHADOW_ALPHA)
