"""Tests for the raw-gamepad-input -> action-name mapping. Mirrors
test_key_mapping.py: pure functions, no real joystick object needed —
just literal button indices / hat tuples in, action string (or None) out.
"""

import pygame

from game.input.gamepad_mapping import map_button, map_hat, axis_to_digital, merge_keys


class FakeJoystick:
    def __init__(self, axes=(0.0, 0.0), hat=(0, 0), has_hat=True):
        self._axes = axes
        self._hat = hat
        self._has_hat = has_hat

    def get_axis(self, index):
        return self._axes[index]

    def get_numhats(self):
        return 1 if self._has_hat else 0

    def get_hat(self, index):
        return self._hat


NO_KEYS = {
    pygame.K_LEFT: False, pygame.K_RIGHT: False,
    pygame.K_UP: False, pygame.K_DOWN: False,
    pygame.K_a: False, pygame.K_d: False,
}


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


def test_merge_keys_with_no_joystick_returns_underlying_keys_unchanged():
    merged = merge_keys(NO_KEYS, joystick=None, deadzone=0.5)
    assert merged[pygame.K_LEFT] == NO_KEYS[pygame.K_LEFT]
    assert merged[pygame.K_a] == NO_KEYS[pygame.K_a]


def test_merge_keys_left_stick_pushed_left_sets_left_true():
    joystick = FakeJoystick(axes=(-1.0, 0.0))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_LEFT] is True
    assert merged[pygame.K_RIGHT] is False


def test_merge_keys_left_stick_pushed_right_sets_right_true():
    joystick = FakeJoystick(axes=(1.0, 0.0))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_RIGHT] is True
    assert merged[pygame.K_LEFT] is False


def test_merge_keys_left_stick_pushed_up_sets_up_true():
    # SDL2 joystick y-axis is inverted: pushing up yields a NEGATIVE value.
    joystick = FakeJoystick(axes=(0.0, -1.0))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_UP] is True
    assert merged[pygame.K_DOWN] is False


def test_merge_keys_left_stick_pushed_down_sets_down_true():
    joystick = FakeJoystick(axes=(0.0, 1.0))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_DOWN] is True
    assert merged[pygame.K_UP] is False


def test_merge_keys_dpad_up_sets_up_true():
    # SDL2 hat y=+1 means up (opposite sign convention from the axis).
    joystick = FakeJoystick(hat=(0, 1))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_UP] is True


def test_merge_keys_dpad_down_sets_down_true():
    joystick = FakeJoystick(hat=(0, -1))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_DOWN] is True


def test_merge_keys_stick_below_deadzone_does_not_set_direction():
    joystick = FakeJoystick(axes=(0.2, 0.2))
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_LEFT] is False
    assert merged[pygame.K_RIGHT] is False
    assert merged[pygame.K_UP] is False
    assert merged[pygame.K_DOWN] is False


def test_merge_keys_joystick_with_no_hat_does_not_crash():
    joystick = FakeJoystick(has_hat=False)
    merged = merge_keys(NO_KEYS, joystick, deadzone=0.5)
    assert merged[pygame.K_UP] is False


def test_merge_keys_leaves_non_directional_keys_untouched():
    keys = dict(NO_KEYS)
    keys[pygame.K_a] = True
    merged = merge_keys(keys, joystick=None, deadzone=0.5)
    assert merged[pygame.K_a] is True


def test_merge_keys_falls_back_to_keyboard_only_if_joystick_read_raises():
    class DisconnectedJoystick:
        def get_axis(self, index):
            raise pygame.error("Joystick has been disconnected")

        def get_numhats(self):
            raise pygame.error("Joystick has been disconnected")

        def get_hat(self, index):
            raise pygame.error("Joystick has been disconnected")

    keys = dict(NO_KEYS)
    keys[pygame.K_a] = True
    merged = merge_keys(keys, DisconnectedJoystick(), deadzone=0.5)
    assert merged[pygame.K_LEFT] is False
    assert merged[pygame.K_a] is True


def test_merge_keys_ors_with_real_key_state_rather_than_overriding():
    keys = dict(NO_KEYS)
    keys[pygame.K_LEFT] = True
    joystick = FakeJoystick(axes=(0.0, 0.0))
    merged = merge_keys(keys, joystick, deadzone=0.5)
    assert merged[pygame.K_LEFT] is True


def test_contexts_do_not_leak_into_each_other():
    # Button 3 means "restart" while playing, but nothing in the menu or editor
    assert map_button("menu", 3) is None
    assert map_button("editor", 3) is None
    # D-pad pans the editor, but does nothing in the menu
    assert map_hat("menu", (-1, 0)) is None
