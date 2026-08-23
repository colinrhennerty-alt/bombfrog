"""Pure math for the depth axis: depth 0.0 is the far edge of the
walkway, 1.0 is the near edge. No pygame dependency — used by both
simulation (game.entities, for movement bounds) and rendering (for
scale/ground position).
"""

from game.config import GROUND_NEAR_Y, GROUND_FAR_Y, FAR_MARGIN, NEAR_SCALE, FAR_SCALE, DEPTH_COLLISION_TOLERANCE


def ground_y_for_depth(depth):
    return GROUND_FAR_Y + depth * (GROUND_NEAR_Y - GROUND_FAR_Y)


def margin_for_depth(depth):
    return FAR_MARGIN * (1 - depth)


def scale_for_depth(depth):
    return FAR_SCALE + depth * (NEAR_SCALE - FAR_SCALE)


def same_plane(depth_a, depth_b, tolerance=DEPTH_COLLISION_TOLERANCE):
    """Are two entities close enough in depth to interact for collision
    purposes?

    Collision detection uses this instead of comparing raw pixel
    y-positions: a large hitbox (e.g. a bomb's full blast radius) can
    span most of the depth range in pixel terms, which would otherwise
    let it "see" entities far away in depth. A continuous tolerance
    rather than discrete bucket/plane numbers — bucketing has two
    failure modes at once: two entities deep inside the same wide
    bucket can still be too far apart to look adjacent, while two
    entities right next to each other can land on opposite sides of a
    bucket boundary and wrongly be treated as unrelated.
    """
    return abs(depth_a - depth_b) <= tolerance
