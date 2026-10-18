"""What blocks movement: tree trunks, checked against a mover's feet.

Movers (Player, Enemy) step one axis at a time and ask `blocks` whether a
step's feet would land on an obstacle, so they slide along a trunk instead
of sticking to it. Only the feet collide, which is what lets a frog walk
behind a tree with its body overlapping the trunk's sprite.
"""

from dataclasses import dataclass

from game.config import TREE_SCALE, TREE_TRUNK_DEPTH, FEET_HEIGHT, FEET_WIDTH_RATIO
from game.simulation.rect import Rect
from game.simulation.trees import kind_named


@dataclass(frozen=True)
class Obstacle:
    rect: Rect
    jumpable: bool  # an airborne frog passes over it


def trunk_obstacle(tree):
    kind = kind_named(tree.kind)
    return Obstacle(
        Rect.from_center(tree.x, tree.y, kind.trunk_art_px * TREE_SCALE, TREE_TRUNK_DEPTH),
        jumpable=kind.jumpable,
    )


def feet_rect(x, y, width, height):
    """The strip along the bottom of a mover's hitbox (top-left x/y, like
    Player/Enemy) that collides with obstacles."""
    return Rect.from_midbottom(x + width / 2, y + height, width * FEET_WIDTH_RATIO, FEET_HEIGHT)


def blocks(obstacles, old_feet, new_feet, airborne=False):
    """Whether stepping from old_feet to new_feet runs into an obstacle.
    A step out of an obstacle the mover already overlaps is always allowed,
    so nothing ever gets stuck inside one."""
    for obstacle in obstacles:
        if airborne and obstacle.jumpable:
            continue
        if obstacle.rect.colliderect(new_feet) and not obstacle.rect.colliderect(old_feet):
            return True
    return False
