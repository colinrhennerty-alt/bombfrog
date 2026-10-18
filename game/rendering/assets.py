"""Loads and slices the player, bomb and enemy critter spritesheets.

Loading is lazy (first call to get_frog_frames()) and cached, because
Surface.convert_alpha() requires an active display mode — it can't run
at import time, since that would run before main.py's
pygame.display.set_mode() has had a chance to execute.
"""

import pygame

from game.config import FROG_IDLE_FRAME_COUNT
from game.paths import resource_path

SHEET_PATH = resource_path("assets/frog_green_spritesheet.png")
BOMB_EXPLOSION_SHEET_PATH = resource_path("assets/bomb_explosion.png")
CRITTERS_DIR = "assets/critters"
CRITTER_FACINGS = ("SE", "SW")
BADGER_FRAME_WIDTH = 42
STAG_FRAME_WIDTH = 32
BOAR_RUN_FRAME_COUNT = 4
CELL = 32

_frames_cache = None
_bomb_explosion_frames_cache = None
_critter_frames_cache = None


def _slice_frame(sheet, col, row):
    return sheet.subsurface(pygame.Rect(col * CELL, row * CELL, CELL, CELL))


def _load_frames():
    """Native-resolution frog frames, all cropped to one shared box; the
    renderer scales them uniformly so the frog is never stretched."""
    sheet = pygame.image.load(SHEET_PATH).convert_alpha()
    idle = [_slice_frame(sheet, col, 0) for col in range(FROG_IDLE_FRAME_COUNT)]
    *idle, jump, land = _crop_to_shared_bounds([*idle, _slice_frame(sheet, 3, 1), _slice_frame(sheet, 4, 3)])
    return {"idle": idle, "jump": jump, "land": land}


def _load_bomb_explosion_frames():
    sheet = pygame.image.load(BOMB_EXPLOSION_SHEET_PATH).convert_alpha()
    return [sheet.subsurface(pygame.Rect(col * CELL, 0, CELL, CELL)) for col in range(4)]


def _slice_strip(sheet, frame_width):
    """Cuts a single-row horizontal strip into equal-width frames."""
    height = sheet.get_height()
    return [
        sheet.subsurface(pygame.Rect(col * frame_width, 0, frame_width, height))
        for col in range(sheet.get_width() // frame_width)
    ]


def _load_strip(relative_path, frame_width):
    sheet = pygame.image.load(resource_path(f"{CRITTERS_DIR}/{relative_path}")).convert_alpha()
    return _slice_strip(sheet, frame_width)


def _load_boar_run(facing):
    # The boar ships one PNG per frame rather than a strip.
    return [
        pygame.image.load(resource_path(f"{CRITTERS_DIR}/boar/boar_{facing}_run_{i}.png")).convert_alpha()
        for i in range(BOAR_RUN_FRAME_COUNT)
    ]


def _crop_to_shared_bounds(frames):
    """Trims transparent padding so the art's lowest pixel sits on the
    frame's bottom edge — draw_enemy scales the frame into the hitbox, so
    leftover padding would float the critter above the ground. One crop
    (the union of every frame's opaque area) for the whole set, so the
    art doesn't jitter from frame to frame."""
    bounds = frames[0].get_bounding_rect(min_alpha=1).unionall(
        [f.get_bounding_rect(min_alpha=1) for f in frames[1:]]
    )
    return [f.subsurface(bounds) for f in frames]


def _load_critter_frames():
    raw = {
        "badger": {
            facing: _load_strip(f"badger/critter_badger_{facing}_walk.png", BADGER_FRAME_WIDTH)
            for facing in CRITTER_FACINGS
        },
        "boar": {facing: _load_boar_run(facing) for facing in CRITTER_FACINGS},
        "stag": {
            facing: _load_strip(f"stag/critter_stag_{facing}_run.png", STAG_FRAME_WIDTH)
            for facing in CRITTER_FACINGS
        },
    }
    return {
        critter: {facing: _crop_to_shared_bounds(frames) for facing, frames in facings.items()}
        for critter, facings in raw.items()
    }


def get_frog_frames():
    global _frames_cache
    if _frames_cache is None:
        _frames_cache = _load_frames()
    return _frames_cache


def get_bomb_explosion_frames():
    global _bomb_explosion_frames_cache
    if _bomb_explosion_frames_cache is None:
        _bomb_explosion_frames_cache = _load_bomb_explosion_frames()
    return _bomb_explosion_frames_cache


def get_bomb_sprite():
    return get_bomb_explosion_frames()[0]


def get_critter_frames():
    global _critter_frames_cache
    if _critter_frames_cache is None:
        _critter_frames_cache = _load_critter_frames()
    return _critter_frames_cache
