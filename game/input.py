"""Raw pygame key -> abstract action name, per UI context.

Deliberately dumb: this only knows "what key, in what context (menu vs.
playing)". Decisions that depend on game state — e.g. whether "space"
means jump or restart — belong to game.scene.GameApp, not here.
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
}


def map_key(state, key):
    table = MENU_KEY_ACTIONS if state == "menu" else PLAYING_KEY_ACTIONS
    return table.get(key)
