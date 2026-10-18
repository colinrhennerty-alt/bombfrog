"""Tests for the raw-key -> Action mapping. Deliberately dumb: it only
knows about pygame key constants and which Mode they apply in — never
game state like world.game_over.
"""

import pygame

from game.input.actions import Action
from game.scene.modes import Mode
from game.input.key_mapping import map_key, EDITOR_KEY_ACTIONS, PLAYING_KEY_ACTIONS, MOVEMENT_KEYS


def test_menu_up_and_down():
    assert map_key(Mode.MENU, pygame.K_UP) == Action.MENU_UP
    assert map_key(Mode.MENU, pygame.K_DOWN) == Action.MENU_DOWN


def test_menu_confirm_from_return_or_space():
    assert map_key(Mode.MENU, pygame.K_RETURN) == Action.MENU_CONFIRM
    assert map_key(Mode.MENU, pygame.K_SPACE) == Action.MENU_CONFIRM


def test_menu_unknown_key_returns_none():
    assert map_key(Mode.MENU, pygame.K_r) is None
    assert map_key(Mode.MENU, pygame.K_z) is None


def test_playing_space_restart_save_load_escape():
    assert map_key(Mode.PLAYING, pygame.K_SPACE) == Action.JUMP
    assert map_key(Mode.PLAYING, pygame.K_r) == Action.RESTART
    assert map_key(Mode.PLAYING, pygame.K_F5) == Action.SAVE
    assert map_key(Mode.PLAYING, pygame.K_F9) == Action.LOAD
    assert map_key(Mode.PLAYING, pygame.K_ESCAPE) == Action.MENU_BACK


def test_playing_f13_toggles_debug():
    assert map_key(Mode.PLAYING, pygame.K_F13) == Action.TOGGLE_DEBUG
    assert map_key(Mode.PLAYING, pygame.K_F1) is None


def test_playing_unknown_key_returns_none():
    assert map_key(Mode.PLAYING, pygame.K_UP) is None
    assert map_key(Mode.PLAYING, pygame.K_RETURN) is None


def test_contexts_do_not_leak_into_each_other():
    # K_r means "restart" while playing, but nothing in the menu
    assert map_key(Mode.MENU, pygame.K_r) is None
    # K_UP navigates the menu, but does nothing while playing
    assert map_key(Mode.PLAYING, pygame.K_UP) is None


def test_editor_arrow_keys_and_wasd_pan():
    assert map_key(Mode.EDITOR, pygame.K_UP) == Action.PAN_UP
    assert map_key(Mode.EDITOR, pygame.K_DOWN) == Action.PAN_DOWN
    assert map_key(Mode.EDITOR, pygame.K_LEFT) == Action.PAN_LEFT
    assert map_key(Mode.EDITOR, pygame.K_RIGHT) == Action.PAN_RIGHT
    assert map_key(Mode.EDITOR, pygame.K_w) == Action.PAN_UP
    assert map_key(Mode.EDITOR, pygame.K_s) == Action.PAN_DOWN
    assert map_key(Mode.EDITOR, pygame.K_a) == Action.PAN_LEFT
    assert map_key(Mode.EDITOR, pygame.K_d) == Action.PAN_RIGHT


def test_editor_number_keys_select_tile_by_index():
    assert map_key(Mode.EDITOR, pygame.K_1) == Action.SELECT_TILE_0
    assert map_key(Mode.EDITOR, pygame.K_0) == Action.SELECT_TILE_9


def test_editor_escape_returns_to_menu():
    assert map_key(Mode.EDITOR, pygame.K_ESCAPE) == Action.MENU_BACK


def test_editor_unknown_key_returns_none():
    assert map_key(Mode.EDITOR, pygame.K_z) is None


def test_editor_context_does_not_leak_into_menu_or_playing():
    assert map_key(Mode.MENU, pygame.K_1) is None
    assert map_key(Mode.PLAYING, pygame.K_1) is None


def test_editor_key_actions_table_has_no_duplicate_conflicting_actions_for_wasd_and_arrows():
    # Each direction should be reachable by exactly one arrow key and one
    # WASD key, both mapping to the same action.
    assert EDITOR_KEY_ACTIONS[pygame.K_UP] == EDITOR_KEY_ACTIONS[pygame.K_w]
    assert EDITOR_KEY_ACTIONS[pygame.K_DOWN] == EDITOR_KEY_ACTIONS[pygame.K_s]
    assert EDITOR_KEY_ACTIONS[pygame.K_LEFT] == EDITOR_KEY_ACTIONS[pygame.K_a]
    assert EDITOR_KEY_ACTIONS[pygame.K_RIGHT] == EDITOR_KEY_ACTIONS[pygame.K_d]


def test_no_playing_action_shares_a_key_with_held_movement():
    # Player movement reads these keys as held every frame; a KEYDOWN action
    # on the same key would fire whenever the player starts moving.
    assert set(MOVEMENT_KEYS).isdisjoint(PLAYING_KEY_ACTIONS)
