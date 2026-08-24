"""Data-driven enemy definitions.

Adding a new enemy type means adding one entry to ENEMY_TYPES — nothing
else in the game needs to change to support it.
"""

import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

ShardSpec = Tuple[float, float, Optional[Tuple[int, int, int]]]  # (angle, speed_multiplier, color)


def _ring(count, speed_multiplier, color=None) -> Callable[[float], List[ShardSpec]]:
    def pattern(direction):
        return [(math.pi * 2 * i / count, speed_multiplier, color) for i in range(count)]

    return pattern


def _cone(count, speed_multiplier, color, spread) -> Callable[[float], List[ShardSpec]]:
    def pattern(direction):
        half = (count - 1) / 2
        return [(direction + (i - half) * spread, speed_multiplier, color) for i in range(count)]

    return pattern


@dataclass(frozen=True)
class EnemyType:
    name: str
    color: Tuple[int, int, int]
    max_hp: int
    spawn_weight: float
    shrapnel_pattern: Callable[[float], List[ShardSpec]]


ENEMY_TYPES = {
    "grunt": EnemyType("grunt", (190, 80, 80), 1, 0.55, _ring(6, 1.1)),
    "heavy": EnemyType("heavy", (170, 130, 80), 2, 0.30, _cone(5, 1.3, (220, 140, 80), 0.3)),
    "elite": EnemyType("elite", (150, 95, 185), 3, 0.15, _ring(8, 0.9, (200, 140, 240))),
}
