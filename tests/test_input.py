"""Tests for the raw-key -> action-name mapping. Deliberately dumb: it
only knows about pygame key constants and which UI context ("menu" vs.
"playing") they apply in — never game state like world.game_over.
"""

import pygame

from game.input import map_key


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


def test_playing_unknown_key_returns_none():
    assert map_key("playing", pygame.K_UP) is None
    assert map_key("playing", pygame.K_RETURN) is None


def test_contexts_do_not_leak_into_each_other():
    # K_r means "restart" while playing, but nothing in the menu
    assert map_key("menu", pygame.K_r) is None
    # K_UP navigates the menu, but does nothing while playing
    assert map_key("playing", pygame.K_UP) is None
