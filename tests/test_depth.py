"""Pure depth-axis math: 0.0 = far edge of the walkway, 1.0 = near edge."""

from game.config import GROUND_NEAR_Y, GROUND_FAR_Y, FAR_MARGIN, NEAR_SCALE, FAR_SCALE
from game.depth import ground_y_for_depth, margin_for_depth, scale_for_depth


def test_ground_y_at_extremes():
    assert ground_y_for_depth(0.0) == GROUND_FAR_Y
    assert ground_y_for_depth(1.0) == GROUND_NEAR_Y


def test_margin_at_extremes():
    assert margin_for_depth(0.0) == FAR_MARGIN
    assert margin_for_depth(1.0) == 0


def test_scale_at_extremes():
    assert scale_for_depth(0.0) == FAR_SCALE
    assert scale_for_depth(1.0) == NEAR_SCALE


def test_values_interpolate_linearly_at_the_midpoint():
    assert ground_y_for_depth(0.5) == (GROUND_FAR_Y + GROUND_NEAR_Y) / 2
    assert margin_for_depth(0.5) == FAR_MARGIN / 2
    assert scale_for_depth(0.5) == (FAR_SCALE + NEAR_SCALE) / 2
