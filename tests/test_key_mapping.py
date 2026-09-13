"""Tests for the raw-key -> action-name mapping. Deliberately dumb: it
only knows about pygame key constants and which UI context ("menu" vs.
"playing") they apply in — never game state like world.game_over.
"""

import pygame

from game.input.key_mapping import map_key, EDITOR_KEY_ACTIONS


def test_menu_up_and_down():
    assert map_key("menu", pygame.K_UP) == "menu_up"
    assert map_key("menu", pygame.K_DOWN) == "menu_down"


def test_menu_confirm_from_return_or_space():
    assert map_key("menu", pygame.K_RETURN) == "menu_confirm"
    assert map_key("menu", pygame.K_SPACE) == "menu_confirm"


def test_menu_unknown_key_returns_none():
    assert map_key("menu", pygame.K_r) is None
    assert map_key("menu", pygame.K_z) is None


def test_playing_space_restart_save_load_escape():
    assert map_key("playing", pygame.K_SPACE) == "space"
    assert map_key("playing", pygame.K_r) == "restart"
    assert map_key("playing", pygame.K_s) == "save"
    assert map_key("playing", pygame.K_l) == "load"
    assert map_key("playing", pygame.K_ESCAPE) == "menu_back"


def test_playing_f13_toggles_debug():
    assert map_key("playing", pygame.K_F13) == "toggle_debug"
    assert map_key("playing", pygame.K_F1) is None


def test_playing_unknown_key_returns_none():
    assert map_key("playing", pygame.K_UP) is None
    assert map_key("playing", pygame.K_RETURN) is None


def test_contexts_do_not_leak_into_each_other():
    # K_r means "restart" while playing, but nothing in the menu
    assert map_key("menu", pygame.K_r) is None
    # K_UP navigates the menu, but does nothing while playing
    assert map_key("playing", pygame.K_UP) is None


def test_editor_arrow_keys_and_wasd_pan():
    assert map_key("editor", pygame.K_UP) == "pan_up"
    assert map_key("editor", pygame.K_DOWN) == "pan_down"
    assert map_key("editor", pygame.K_LEFT) == "pan_left"
    assert map_key("editor", pygame.K_RIGHT) == "pan_right"
    assert map_key("editor", pygame.K_w) == "pan_up"
    assert map_key("editor", pygame.K_s) == "pan_down"
    assert map_key("editor", pygame.K_a) == "pan_left"
    assert map_key("editor", pygame.K_d) == "pan_right"


def test_editor_number_keys_select_tile_by_index():
    assert map_key("editor", pygame.K_1) == "select_tile_0"
    assert map_key("editor", pygame.K_0) == "select_tile_9"


def test_editor_save_load_escape():
    assert map_key("editor", pygame.K_F5) == "save_level"
    assert map_key("editor", pygame.K_F9) == "load_level"
    assert map_key("editor", pygame.K_ESCAPE) == "menu_back"


def test_editor_unknown_key_returns_none():
    assert map_key("editor", pygame.K_z) is None


def test_editor_context_does_not_leak_into_menu_or_playing():
    assert map_key("menu", pygame.K_F5) is None
    assert map_key("playing", pygame.K_F5) is None


def test_editor_key_actions_table_has_no_duplicate_conflicting_actions_for_wasd_and_arrows():
    # Each direction should be reachable by exactly one arrow key and one
    # WASD key, both mapping to the same action.
    assert EDITOR_KEY_ACTIONS[pygame.K_UP] == EDITOR_KEY_ACTIONS[pygame.K_w]
    assert EDITOR_KEY_ACTIONS[pygame.K_DOWN] == EDITOR_KEY_ACTIONS[pygame.K_s]
    assert EDITOR_KEY_ACTIONS[pygame.K_LEFT] == EDITOR_KEY_ACTIONS[pygame.K_a]
    assert EDITOR_KEY_ACTIONS[pygame.K_RIGHT] == EDITOR_KEY_ACTIONS[pygame.K_d]
