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


# How big an enemy may be next to the frog, by height. Stylized rather than
# realistic (a real stag is ~100 frogs tall); the frog must still be able
# to jump over every enemy (tests/test_jump_clearance.py). Ratios are tuned
# by how big each critter *reads*, not by height alone — the stag is mostly
# legs and antlers, so it needs much more height than the solid boar to
# read biggest (tests/test_visual_size.py).
HEIGHT_VS_FROG_RANGE = (0.5, 4.0)


@dataclass(frozen=True)
class EnemyType:
    name: str
    color: Tuple[int, int, int]
    max_hp: int
    spawn_weight: float
    shrapnel_pattern: Callable[[float], List[ShardSpec]]
    sprite: str  # key into game.rendering.assets.get_critter_frames()
    height_vs_frog: float  # hitbox height as a multiple of the frog's
    art_aspect: float  # width / height of the cropped critter art

    def __post_init__(self):
        low, high = HEIGHT_VS_FROG_RANGE
        if not low <= self.height_vs_frog <= high:
            raise ValueError(
                f"{self.name}: height_vs_frog {self.height_vs_frog} is outside {HEIGHT_VS_FROG_RANGE}"
            )


ENEMY_TYPES = {
    "grunt": EnemyType(
        "grunt", (190, 80, 80), max_hp=1, spawn_weight=0.55, shrapnel_pattern=_ring(6, 1.1),
        sprite="badger", height_vs_frog=1.5, art_aspect=26 / 20,
    ),
    "heavy": EnemyType(
        "heavy", (170, 130, 80), max_hp=2, spawn_weight=0.30, shrapnel_pattern=_cone(5, 1.3, (220, 140, 80), 0.3),
        sprite="boar", height_vs_frog=1.6, art_aspect=34 / 24,
    ),
    "elite": EnemyType(
        "elite", (150, 95, 185), max_hp=3, spawn_weight=0.15, shrapnel_pattern=_ring(8, 0.9, (200, 140, 240)),
        sprite="stag", height_vs_frog=3.5, art_aspect=27 / 40,
    ),
}
