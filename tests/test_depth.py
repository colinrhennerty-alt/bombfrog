"""Pure depth-axis math: 0.0 = far edge of the walkway, 1.0 = near edge."""

from game.config import GROUND_NEAR_Y, GROUND_FAR_Y, FAR_MARGIN, NEAR_SCALE, FAR_SCALE
from game.depth import ground_y_for_depth, margin_for_depth, scale_for_depth, depth_plane, same_plane


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


# --- z-plane bucketing -----------------------------------------------------
# The walkway is drawn with two perspective gridlines at t=0.33/0.66
# (game.rendering.draw_ground), splitting it into three visual bands: far,
# mid, near. Collision detection uses the same three bands, rather than a
# pixel-based y-proximity proxy, which breaks down whenever an entity's
# hitbox (e.g. a bomb's full blast radius) is large relative to the whole
# depth range.


def test_depth_plane_has_three_buckets_matching_the_ground_gridlines():
    assert depth_plane(0.0) == depth_plane(0.32)
    assert depth_plane(0.34) == depth_plane(0.65)
    assert depth_plane(0.67) == depth_plane(1.0)

    assert depth_plane(0.0) != depth_plane(0.5)
    assert depth_plane(0.5) != depth_plane(1.0)
    assert depth_plane(0.0) != depth_plane(1.0)


def test_same_plane_true_within_a_band():
    assert same_plane(0.1, 0.2) is True
    assert same_plane(0.5, 0.66) is True
    assert same_plane(0.7, 0.99) is True


def test_same_plane_false_across_bands():
    assert same_plane(0.1, 0.9) is False
    assert same_plane(0.0, 0.5) is False
    assert same_plane(0.5, 1.0) is False
