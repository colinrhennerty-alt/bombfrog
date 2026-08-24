"""Tests for GameApp: the menu <-> playing <-> game-over state machine
that used to live as loose local variables inside main.py's run_game().
"""

import pygame

from game.config import SAVE_FILE
from game.entities import Player
from game.persistence import save_game
from game.scene import GameApp

NO_KEYS = {
    pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False,
}


def test_app_starts_in_menu_with_no_world():
    app = GameApp()
    assert app.state == "menu"
    assert app.world is None
    assert app.running is True
    assert app.selected == 0
    assert app.menu_options == ["Start Game", "Load Game", "Quit"]
    assert app.high_score == 0
    assert app.debug is False


def test_default_save_file_matches_config():
    assert GameApp().save_file == SAVE_FILE


def test_debug_can_be_set_at_construction():
    assert GameApp(debug=True).debug is True
    assert GameApp(debug=False).debug is False
    assert GameApp().debug is False  # default unchanged


def test_menu_navigation_wraps_in_both_directions():
    app = GameApp()
    app.handle_action("menu_up", now=0)
    assert app.selected == len(app.menu_options) - 1  # wraps backward past 0

    app.selected = 0
    app.handle_action("menu_down", now=0)
    assert app.selected == 1
    app.handle_action("menu_down", now=0)
    app.handle_action("menu_down", now=0)
    assert app.selected == 0  # wraps forward past the end


def test_menu_confirm_start_game_creates_world_and_switches_to_playing():
    app = GameApp()
    app.selected = 0  # "Start Game"
    app.handle_action("menu_confirm", now=123)
    assert app.state == "playing"
    assert app.world is not None
    assert app.world.last_spawn == 123


def test_menu_confirm_load_game_missing_file_is_a_noop(tmp_path):
    app = GameApp(save_file=str(tmp_path / "missing.json"))
    app.selected = 1  # "Load Game"
    app.handle_action("menu_confirm", now=0)
    assert app.state == "menu"
    assert app.world is None


def test_menu_confirm_load_game_with_valid_save(tmp_path):
    save_path = str(tmp_path / "save.json")
    save_game(save_path, Player(), [], [], [], score=42, high_score=99, lives=2, last_spawn=777)

    app = GameApp(save_file=save_path)
    app.selected = 1  # "Load Game"
    app.handle_action("menu_confirm", now=555)

    assert app.state == "playing"
    assert app.world.score == 42
    assert app.world.lives == 2
    assert app.high_score == 99


def test_menu_confirm_quit_stops_running():
    app = GameApp()
    app.selected = 2  # "Quit"
    app.handle_action("menu_confirm", now=0)
    assert app.running is False


def _started_app(now=0):
    app = GameApp()
    app.selected = 0
    app.handle_action("menu_confirm", now=now)
    return app


def test_space_jumps_when_not_game_over():
    app = _started_app()
    bombs_before = app.world.player.bombs_left

    app.handle_action("space", now=1)

    assert app.world.player.on_ground is False
    assert app.world.player.bombs_left == bombs_before - 1


def test_space_restarts_when_game_over():
    app = _started_app()
    app.world.game_over = True
    app.world.score = 999

    app.handle_action("space", now=42)

    assert app.world.game_over is False
    assert app.world.score == 0  # a full reset, not a respawn


def test_restart_is_a_noop_unless_game_over():
    app = _started_app()
    app.world.score = 10
    app.handle_action("restart", now=0)
    assert app.world.score == 10  # untouched

    app.world.game_over = True
    app.handle_action("restart", now=0)
    assert app.world.game_over is False
    assert app.world.score == 0


def test_save_and_load_round_trip(tmp_path):
    app = GameApp(save_file=str(tmp_path / "save.json"))
    app.selected = 0
    app.handle_action("menu_confirm", now=0)
    app.world.score = 321

    app.handle_action("save", now=0)
    app.world.score = 0
    app.handle_action("load", now=0)

    assert app.world.score == 321


def test_menu_back_returns_to_menu():
    app = _started_app()
    app.handle_action("menu_back", now=0)
    assert app.state == "menu"


def test_toggle_debug_flips_the_flag():
    app = _started_app()
    assert app.debug is False

    app.handle_action("toggle_debug", now=0)
    assert app.debug is True

    app.handle_action("toggle_debug", now=0)
    assert app.debug is False


def test_tick_is_a_noop_in_menu_state():
    app = GameApp()
    app.tick(NO_KEYS, dt=16, now=1000)
    assert app.world is None


def test_tick_updates_high_score_once_the_round_is_over():
    app = _started_app()
    app.world.game_over = True
    app.world.score = 555

    app.tick(NO_KEYS, dt=16, now=1000)

    assert app.high_score == 555


def test_tick_syncs_world_debug_flag_to_the_apps():
    app = _started_app()
    assert app.world.debug is False

    app.handle_action("toggle_debug", now=0)
    app.tick(NO_KEYS, dt=16, now=1000)
    assert app.world.debug is True

    app.handle_action("toggle_debug", now=0)
    app.tick(NO_KEYS, dt=16, now=1000)
    assert app.world.debug is False
