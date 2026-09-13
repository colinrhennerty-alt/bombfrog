"""Tests for the raw-gamepad-input -> action-name mapping. Mirrors
test_key_mapping.py: pure functions, no real joystick object needed —
just literal button indices / hat tuples in, action string (or None) out.
"""

from game.input.gamepad_mapping import map_button, map_hat, axis_to_digital


def test_menu_confirm_from_button_a():
    assert map_button("menu", 0) == "menu_confirm"


def test_menu_dpad_up_and_down():
    assert map_hat("menu", (0, 1)) == "menu_up"
    assert map_hat("menu", (0, -1)) == "menu_down"


def test_menu_unknown_button_returns_none():
    assert map_button("menu", 1) is None
    assert map_button("menu", 99) is None


def test_playing_space_from_button_a():
    assert map_button("playing", 0) == "space"


def test_playing_restart_from_button_y():
    assert map_button("playing", 3) == "restart"


def test_playing_menu_back_from_button_b():
    assert map_button("playing", 1) == "menu_back"


def test_playing_unknown_button_returns_none():
    assert map_button("playing", 2) is None


def test_playing_dpad_does_nothing():
    assert map_hat("playing", (0, 1)) is None
    assert map_hat("playing", (0, -1)) is None
    assert map_hat("playing", (-1, 0)) is None
    assert map_hat("playing", (1, 0)) is None


def test_editor_dpad_pans_in_all_four_directions():
    assert map_hat("editor", (0, 1)) == "pan_up"
    assert map_hat("editor", (0, -1)) == "pan_down"
    assert map_hat("editor", (-1, 0)) == "pan_left"
    assert map_hat("editor", (1, 0)) == "pan_right"


def test_editor_menu_back_from_button_b():
    assert map_button("editor", 1) == "menu_back"


def test_editor_unknown_button_returns_none():
    assert map_button("editor", 0) is None


def test_hat_center_returns_none_in_every_context():
    assert map_hat("menu", (0, 0)) is None
    assert map_hat("playing", (0, 0)) is None
    assert map_hat("editor", (0, 0)) is None


def test_axis_to_digital_below_deadzone_returns_zero():
    assert axis_to_digital(0.0, deadzone=0.5) == 0
    assert axis_to_digital(0.49, deadzone=0.5) == 0
    assert axis_to_digital(-0.49, deadzone=0.5) == 0


def test_axis_to_digital_at_or_past_deadzone_returns_signed_direction():
    assert axis_to_digital(0.5, deadzone=0.5) == 1
    assert axis_to_digital(1.0, deadzone=0.5) == 1
    assert axis_to_digital(-0.5, deadzone=0.5) == -1
    assert axis_to_digital(-1.0, deadzone=0.5) == -1


def test_contexts_do_not_leak_into_each_other():
    # Button 3 means "restart" while playing, but nothing in the menu or editor
    assert map_button("menu", 3) is None
    assert map_button("editor", 3) is None
    # D-pad pans the editor, but does nothing in the menu
    assert map_hat("menu", (-1, 0)) is None
