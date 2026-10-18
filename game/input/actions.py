"""Every abstract action a key press can produce.

game.input.key_mapping turns keys into these; game.scene.game_app decides
what each one does in the current mode.
"""

from enum import StrEnum


class Action(StrEnum):
    # Menu
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"
    MENU_CONFIRM = "menu_confirm"
    MENU_BACK = "menu_back"

    # Playing
    JUMP = "jump"  # also restarts once the round is over
    RESTART = "restart"
    SAVE = "save"
    LOAD = "load"
    TOGGLE_DEBUG = "toggle_debug"

    # Editor
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    SELECT_TILE_0 = "select_tile_0"
    SELECT_TILE_1 = "select_tile_1"
    SELECT_TILE_2 = "select_tile_2"
    SELECT_TILE_3 = "select_tile_3"
    SELECT_TILE_4 = "select_tile_4"
    SELECT_TILE_5 = "select_tile_5"
    SELECT_TILE_6 = "select_tile_6"
    SELECT_TILE_7 = "select_tile_7"
    SELECT_TILE_8 = "select_tile_8"
    SELECT_TILE_9 = "select_tile_9"


# Palette index for each tile-select action, in order: SELECT_TILE_ACTIONS[i]
# selects palette tile i.
SELECT_TILE_ACTIONS = tuple(Action[f"SELECT_TILE_{i}"] for i in range(10))
