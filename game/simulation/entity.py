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
