"""Tests for GameApp: the menu <-> playing <-> game-over state machine
that used to live as loose local variables inside main.py's run_game().
"""

import pygame

from game.config import SAVE_FILE
from game.simulation.player import Player
from game.persistence.save_load import save_game
from game.scene.game_app import GameApp

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
    assert app.menu_options == ["Start Game", "Load Game", "Map Editor", "Quit"]
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
    for _ in range(len(app.menu_options)):
        app.handle_action("menu_down", now=0)
    assert app.selected == 0  # wraps forward past the end, back to start


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
    app.selected = 3  # "Quit"
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


def test_save_action_does_not_reach_into_worlds_internals():
    # GameApp shouldn't need to know World's field names to save it —
    # World.save should own assembling its own save payload.
    app = _started_app()
    app.world.score = 321
    calls = []
    app.world.save = lambda filename, high_score: calls.append((filename, high_score))

    app.handle_action("save", now=0)

    assert calls == [(app.save_file, app.high_score)]


def test_menu_back_returns_to_menu():
    app = _started_app()
    app.handle_action("menu_back", now=0)
    assert app.state == "menu"


def test_menu_confirm_map_editor_creates_editor_state_and_switches_to_editor():
    app = GameApp()
    app.selected = 2  # "Map Editor"
    app.handle_action("menu_confirm", now=0)
    assert app.state == "editor"
    assert app.editor_state is not None


def _editor_app():
    app = GameApp()
    app.selected = 2  # "Map Editor"
    app.handle_action("menu_confirm", now=0)
    return app


def test_editor_pan_actions_move_the_camera():
    app = _editor_app()
    app.editor_state.camera.x, app.editor_state.camera.y = 500, 500

    app.handle_action("pan_right", now=0)
    assert app.editor_state.camera.x > 500

    app.handle_action("pan_left", now=0)
    app.handle_action("pan_left", now=0)
    assert app.editor_state.camera.x < 500

    app.handle_action("pan_down", now=0)
    assert app.editor_state.camera.y > 500

    app.handle_action("pan_up", now=0)
    app.handle_action("pan_up", now=0)
    assert app.editor_state.camera.y < 500


def test_editor_select_tile_action_changes_selected_index():
    app = _editor_app()
    app.handle_action("select_tile_2", now=0)
    assert app.editor_state.selected_index == 2


def test_editor_save_and_load_round_trip(tmp_path):
    app = GameApp(level_file=str(tmp_path / "level.json"))
    app.selected = 2
    app.handle_action("menu_confirm", now=0)

    app.editor_state.tilemap.set_tile(3, 3, app.editor_state.palette[0])
    app.handle_action("save_level", now=0)

    app.editor_state.tilemap.set_tile(3, 3, None)
    app.handle_action("load_level", now=0)

    assert app.editor_state.tilemap.get_tile(3, 3) == app.editor_state.palette[0]


def test_editor_menu_back_returns_to_menu():
    app = _editor_app()
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
