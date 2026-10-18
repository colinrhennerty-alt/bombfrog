"""Cosmetic tree groves scattered over each round's meadow.

A round gets a handful of grove centers; each grove plants a few trees
around its center. Trees stay off the stone border, off tilled soil and
away from the frog's spawn, and never crowd each other. Like GROUND_KINDS,
a new kind of tree is one entry in TREE_KINDS (named after its sprite in
assets/gridwright/trees). Purely cosmetic: nothing here blocks movement.
"""

import math
from dataclasses import dataclass

from game.config import (
    WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, TREE_GROVES, TREES_PER_GROVE, TREE_GROVE_RADIUS,
    TREE_MIN_SPACING, TREE_BORDER_MARGIN, TREE_SPAWN_CLEARANCE,
)
from game.simulation.terrain import GROUND_KINDS, cell_at_px


@dataclass(frozen=True)
class TreeKind:
    name: str
    weight: float


TREE_KINDS = [
    TreeKind("tree_oak_large", 4),
    TreeKind("tree_oak_small", 4),
    TreeKind("tree_birch", 4),
    TreeKind("tree_pine", 4),
    TreeKind("tree_oak_autumn", 1),
    TreeKind("tree_oak_blossom", 1),
    TreeKind("tree_dead", 0.5),
]


@dataclass(frozen=True)
class Tree:
    kind: str
    x: float  # world px of the trunk's base
    y: float


# Each grove tries this many spots per tree it wants, so a crowded grove
# just ends up smaller instead of looping forever.
ATTEMPTS_PER_TREE = 6

_TILLED_TILES = frozenset(next(kind for kind in GROUND_KINDS if kind.name == "tilled").tile_ids)


def _spawn_point():
    # Player() spawns centered in the world (game.simulation.player).
    return WORLD_WIDTH / 2, WORLD_HEIGHT / 2


def generate_trees(rng, ground):
    edge = WORLD_BORDER + TREE_BORDER_MARGIN
    spawn = _spawn_point()
    trees = []

    def fits(x, y):
        return (
            edge <= x <= WORLD_WIDTH - edge
            and edge <= y <= WORLD_HEIGHT - edge
            and math.dist((x, y), spawn) >= TREE_SPAWN_CLEARANCE
            and ground.get_tile(*cell_at_px(x, y)) not in _TILLED_TILES
            and all(math.dist((x, y), (t.x, t.y)) >= TREE_MIN_SPACING for t in trees)
        )

    for _ in range(rng.randint(*TREE_GROVES)):
        center_x = rng.uniform(edge, WORLD_WIDTH - edge)
        center_y = rng.uniform(edge, WORLD_HEIGHT - edge)
        wanted = rng.randint(*TREES_PER_GROVE)
        planted = 0
        for _ in range(wanted * ATTEMPTS_PER_TREE):
            if planted == wanted:
                break
            angle = rng.uniform(0, 2 * math.pi)
            reach = TREE_GROVE_RADIUS * math.sqrt(rng.random())
            x, y = center_x + math.cos(angle) * reach, center_y + math.sin(angle) * reach
            if fits(x, y):
                kind = rng.choices(TREE_KINDS, weights=[k.weight for k in TREE_KINDS])[0]
                trees.append(Tree(kind.name, x, y))
                planted += 1
    return trees
