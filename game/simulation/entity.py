"""The implicit contract every drawable/simulated entity (Player, Bomb,
Shard, Enemy) satisfies via duck typing. Declared here as a Protocol so
the contract is self-documenting instead of only discoverable by reading
game.rendering.renderer's getattr/hasattr fallbacks.
"""

from typing import Protocol, Tuple, runtime_checkable

import pygame


@runtime_checkable
class Entity(Protocol):
    x: float
    y: float
    rect: pygame.Rect

    @property
    def shadow_anchor(self) -> Tuple[float, float]:
        """Where rendering should anchor this entity's shadow."""
        ...

    @property
    def shadow_radius(self) -> float:
        """The base size rendering should draw this entity's shadow at
        (before the height-offset shrink) — an entity's own on-screen
        footprint, so a new entity shape never needs a renderer-side
        hasattr/getattr fallback."""
        ...

    @property
    def shadow_height_offset(self) -> float:
        """How far above the ground this entity currently is, in the same
        units/convention as jump_offset/fall_offset (0 = grounded). Used
        to shrink and fade the shadow as the entity rises."""
        ...
