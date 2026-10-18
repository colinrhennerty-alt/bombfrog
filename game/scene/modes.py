"""The top-level modes GameApp can be in."""

from enum import StrEnum


class Mode(StrEnum):
    MENU = "menu"
    PLAYING = "playing"
    EDITOR = "editor"
