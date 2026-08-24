"""Tiny debug-mode logger, only ever called when World.debug is on.

Centralized here rather than scattering print() calls through
game.world, so the format is consistent and tests can capture output
in one place.
"""


def log(message):
    print(f"[debug] {message}")
