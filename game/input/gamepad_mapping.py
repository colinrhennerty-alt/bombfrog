"""Raw gamepad input -> abstract action name, per UI context.

Mirrors key_mapping.py's shape and intent: this only knows "what
button/hat direction, in what context (menu vs. playing vs. editor)".
Deliberately produces the same action-string vocabulary key_mapping.py
does, so GameApp.handle_action needs no gamepad-specific branches.

Button indices follow the SDL2 standard gamepad mapping (consistent
across Xbox/PlayStation/Switch Pro controllers as reported by
pygame.joystick): 0=A, 1=B, 3=Y.
"""

import pygame

BUTTON_A = 0
BUTTON_B = 1
BUTTON_Y = 3

MENU_BUTTON_ACTIONS = {
    BUTTON_A: "menu_confirm",
}

PLAYING_BUTTON_ACTIONS = {
    BUTTON_A: "space",
    BUTTON_Y: "restart",
    BUTTON_B: "menu_back",
}

EDITOR_BUTTON_ACTIONS = {
    BUTTON_B: "menu_back",
}

_STATE_BUTTON_ACTIONS = {
    "menu": MENU_BUTTON_ACTIONS,
    "editor": EDITOR_BUTTON_ACTIONS,
}

MENU_HAT_ACTIONS = {
    (0, 1): "menu_up",
    (0, -1): "menu_down",
}

EDITOR_HAT_ACTIONS = {
    (0, 1): "pan_up",
    (0, -1): "pan_down",
    (-1, 0): "pan_left",
    (1, 0): "pan_right",
}

_STATE_HAT_ACTIONS = {
    "menu": MENU_HAT_ACTIONS,
    "editor": EDITOR_HAT_ACTIONS,
}


def map_button(state, button):
    table = _STATE_BUTTON_ACTIONS.get(state, PLAYING_BUTTON_ACTIONS)
    return table.get(button)


def map_hat(state, hat_value):
    table = _STATE_HAT_ACTIONS.get(state, {})
    return table.get(hat_value)


def axis_to_digital(value, deadzone):
    """Collapse an analog stick axis reading to -1/0/1, like a d-pad."""
    if value >= deadzone:
        return 1
    if value <= -deadzone:
        return -1
    return 0


class _MergedKeys:
    """A pygame.key.get_pressed()-like object that also reports a
    connected gamepad's left stick / d-pad as digital arrow-key state,
    so Player/World never need to know a controller exists."""

    def __init__(self, keys, left, right, up, down):
        self._keys = keys
        self._left = left
        self._right = right
        self._up = up
        self._down = down

    def __getitem__(self, key):
        if key == pygame.K_LEFT:
            return self._keys[key] or self._left
        if key == pygame.K_RIGHT:
            return self._keys[key] or self._right
        if key == pygame.K_UP:
            return self._keys[key] or self._up
        if key == pygame.K_DOWN:
            return self._keys[key] or self._down
        return self._keys[key]


def merge_keys(keys, joystick, deadzone):
    """Wrap a keys-like object, ORing in a connected joystick's left
    stick / d-pad as digital direction. `joystick` may be None (no
    controller connected) or a real/fake object exposing get_axis,
    get_numhats, get_hat — matching pygame.joystick.Joystick's API.

    SDL2's joystick axis 1 (vertical) is inverted relative to its hat:
    stick-up reads as a NEGATIVE axis value, while hat y=+1 means up.
    Both conventions are normalized here to the same up/down booleans.

    If reading the joystick raises (e.g. it was unplugged mid-session),
    this falls back to keyboard-only for that frame rather than
    crashing the game.
    """
    left = right = up = down = False
    if joystick is not None:
        try:
            x = axis_to_digital(joystick.get_axis(0), deadzone)
            y = axis_to_digital(joystick.get_axis(1), deadzone)
            hat_x, hat_y = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)
        except Exception:
            x = y = hat_x = hat_y = 0
        left = x == -1 or hat_x == -1
        right = x == 1 or hat_x == 1
        up = y == -1 or hat_y == 1
        down = y == 1 or hat_y == -1
    return _MergedKeys(keys, left, right, up, down)
