"""Loads and slices the player spritesheet.

Loading is lazy (first call to get_frog_frames()) and cached, because
Surface.convert_alpha() requires an active display mode — it can't run
at import time, since that would run before main.py's
pygame.display.set_mode() has had a chance to execute.
"""

import pygame

from game.config import FROG_IDLE_FRAME_COUNT

SHEET_PATH = "assets/frog_green_spritesheet.png"
CELL = 32
SPRITE_SIZE = 64

_frames_cache = None


def _slice_frame(sheet, col, row):
    cell = sheet.subsurface(pygame.Rect(col * CELL, row * CELL, CELL, CELL))
    return pygame.transform.scale(cell, (SPRITE_SIZE, SPRITE_SIZE))


def _load_frames():
    sheet = pygame.image.load(SHEET_PATH).convert_alpha()
    return {
        "idle": [_slice_frame(sheet, col, 0) for col in range(FROG_IDLE_FRAME_COUNT)],
        "jump": _slice_frame(sheet, 3, 1),
        "land": _slice_frame(sheet, 4, 3),
    }


def get_frog_frames():
    global _frames_cache
    if _frames_cache is None:
        _frames_cache = _load_frames()
    return _frames_cache
