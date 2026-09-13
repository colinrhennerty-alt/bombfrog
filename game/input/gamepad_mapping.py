"""Raw gamepad input -> abstract action name, per UI context.

Mirrors key_mapping.py's shape and intent: this only knows "what
button/hat direction, in what context (menu vs. playing vs. editor)".
Deliberately produces the same action-string vocabulary key_mapping.py
does, so GameApp.handle_action needs no gamepad-specific branches.

Button indices follow the SDL2 standard gamepad mapping (consistent
across Xbox/PlayStation/Switch Pro controllers as reported by
pygame.joystick): 0=A, 1=B, 3=Y.
"""

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
