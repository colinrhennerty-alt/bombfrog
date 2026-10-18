"""Immutable world-space point."""

from dataclasses import dataclass

from game.utils import clamp


@dataclass(frozen=True)
class Position:
    """A world-space point, with clamping to arena bounds."""

    x: float
    y: float

    def clamped(self, min_x, max_x, min_y, max_y) -> "Position":
        return Position(clamp(self.x, min_x, max_x), clamp(self.y, min_y, max_y))
