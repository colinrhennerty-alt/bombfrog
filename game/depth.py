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
