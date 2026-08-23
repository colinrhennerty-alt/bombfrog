"""Pure math for the depth axis: depth 0.0 is the far edge of the
walkway, 1.0 is the near edge. No pygame dependency — used by both
simulation (game.entities, for movement bounds) and rendering (for
scale/ground position).
"""

from game.config import GROUND_NEAR_Y, GROUND_FAR_Y, FAR_MARGIN, NEAR_SCALE, FAR_SCALE


def ground_y_for_depth(depth):
    return GROUND_FAR_Y + depth * (GROUND_NEAR_Y - GROUND_FAR_Y)


def margin_for_depth(depth):
    return FAR_MARGIN * (1 - depth)


def scale_for_depth(depth):
    return FAR_SCALE + depth * (NEAR_SCALE - FAR_SCALE)


PLANE_COUNT = 3  # matches the two gridlines game.rendering.draw_ground draws (t=0.33/0.66)


def depth_plane(depth):
    """Which of the three visual bands (far/mid/near) a depth falls in.

    Collision detection uses this instead of comparing raw pixel
    y-positions: a large hitbox (e.g. a bomb's full blast radius) can
    span most of the depth range in pixel terms, which would otherwise
    let it "see" entities several planes away.
    """
    plane = int(depth * PLANE_COUNT)
    return min(plane, PLANE_COUNT - 1)  # depth == 1.0 must stay in the last plane


def same_plane(depth_a, depth_b):
    return depth_plane(depth_a) == depth_plane(depth_b)
