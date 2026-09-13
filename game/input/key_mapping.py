"""Raw pygame key -> abstract action name, per UI context.

Deliberately dumb: this only knows "what key, in what context (menu vs.
playing)". Decisions that depend on game state — e.g. whether "space"
means jump or restart — belong to game.scene.game_app.GameApp, not here.
"""

import pygame

MENU_KEY_ACTIONS = {
    pygame.K_UP: "menu_up",
    pygame.K_DOWN: "menu_down",
    pygame.K_RETURN: "menu_confirm",
    pygame.K_SPACE: "menu_confirm",
}

PLAYING_KEY_ACTIONS = {
    pygame.K_SPACE: "space",
    pygame.K_r: "restart",
    pygame.K_s: "save",
    pygame.K_l: "load",
    pygame.K_ESCAPE: "menu_back",
    pygame.K_F13: "toggle_debug",
}

EDITOR_KEY_ACTIONS = {
    pygame.K_UP: "pan_up",
    pygame.K_DOWN: "pan_down",
    pygame.K_LEFT: "pan_left",
    pygame.K_RIGHT: "pan_right",
    pygame.K_w: "pan_up",
    pygame.K_s: "pan_down",
    pygame.K_a: "pan_left",
    pygame.K_d: "pan_right",
    pygame.K_1: "select_tile_0",
    pygame.K_2: "select_tile_1",
    pygame.K_3: "select_tile_2",
    pygame.K_4: "select_tile_3",
    pygame.K_5: "select_tile_4",
    pygame.K_6: "select_tile_5",
    pygame.K_7: "select_tile_6",
    pygame.K_8: "select_tile_7",
    pygame.K_9: "select_tile_8",
    pygame.K_0: "select_tile_9",
    pygame.K_ESCAPE: "menu_back",
}

_STATE_KEY_ACTIONS = {
    "menu": MENU_KEY_ACTIONS,
    "editor": EDITOR_KEY_ACTIONS,
}


def map_key(state, key):
    table = _STATE_KEY_ACTIONS.get(state, PLAYING_KEY_ACTIONS)
    return table.get(key)
