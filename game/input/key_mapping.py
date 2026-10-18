"""Raw pygame key -> abstract Action, per Mode.

Deliberately dumb: this only knows "what key, in what mode". Decisions
that depend on game state — e.g. whether JUMP means jump or restart —
belong to game.scene.game_app.GameApp, not here.
"""

import pygame

from game.input.actions import Action, SELECT_TILE_ACTIONS
from game.scene.modes import Mode

MENU_KEY_ACTIONS = {
    pygame.K_UP: Action.MENU_UP,
    pygame.K_DOWN: Action.MENU_DOWN,
    pygame.K_RETURN: Action.MENU_CONFIRM,
    pygame.K_SPACE: Action.MENU_CONFIRM,
}

PLAYING_KEY_ACTIONS = {
    pygame.K_SPACE: Action.JUMP,
    pygame.K_r: Action.RESTART,
    pygame.K_s: Action.SAVE,
    pygame.K_l: Action.LOAD,
    pygame.K_ESCAPE: Action.MENU_BACK,
    pygame.K_F13: Action.TOGGLE_DEBUG,
}

_TILE_SELECT_KEYS = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
    pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0,
)

EDITOR_KEY_ACTIONS = {
    pygame.K_UP: Action.PAN_UP,
    pygame.K_DOWN: Action.PAN_DOWN,
    pygame.K_LEFT: Action.PAN_LEFT,
    pygame.K_RIGHT: Action.PAN_RIGHT,
    pygame.K_w: Action.PAN_UP,
    pygame.K_s: Action.PAN_DOWN,
    pygame.K_a: Action.PAN_LEFT,
    pygame.K_d: Action.PAN_RIGHT,
    **dict(zip(_TILE_SELECT_KEYS, SELECT_TILE_ACTIONS)),
    pygame.K_ESCAPE: Action.MENU_BACK,
}

_MODE_KEY_ACTIONS = {
    Mode.MENU: MENU_KEY_ACTIONS,
    Mode.PLAYING: PLAYING_KEY_ACTIONS,
    Mode.EDITOR: EDITOR_KEY_ACTIONS,
}


def map_key(mode, key):
    return _MODE_KEY_ACTIONS[mode].get(key)
