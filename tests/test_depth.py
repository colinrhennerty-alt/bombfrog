"""Pure depth-axis math: 0.0 = far edge of the walkway, 1.0 = near edge."""

from game.config import GROUND_NEAR_Y, GROUND_FAR_Y, FAR_MARGIN, NEAR_SCALE, FAR_SCALE, DEPTH_COLLISION_TOLERANCE
from game.depth import ground_y_for_depth, margin_for_depth, scale_for_depth, same_plane


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


# --- z-plane matching -------------------------------------------------------
# Collision detection uses this instead of a pixel-based y-proximity proxy,
# which breaks down whenever an entity's hitbox (e.g. a bomb's full blast
# radius) is large relative to the whole depth range. A continuous
# tolerance rather than discrete bucket/plane numbers: bucketing has two
# failure modes at once — two entities deep inside the same wide bucket
# can still be too far apart to look adjacent, while two entities right
# next to each other can land on opposite sides of a bucket boundary and
# wrongly be treated as unrelated. A tolerance band has neither.


def test_same_plane_true_within_the_tolerance():
    assert same_plane(0.5, 0.5) is True
    assert same_plane(0.5, 0.5 + DEPTH_COLLISION_TOLERANCE - 0.01) is True
    assert same_plane(0.5, 0.5 - DEPTH_COLLISION_TOLERANCE + 0.01) is True


def test_same_plane_false_beyond_the_tolerance():
    assert same_plane(0.5, 0.5 + DEPTH_COLLISION_TOLERANCE + 0.01) is False
    assert same_plane(0.1, 0.9) is False


def test_same_plane_handles_entities_adjacent_across_a_wide_bucket():
    # The old discrete-bucket design could call these "same plane" even
    # though they're ~54px of ground_y apart (about 0.32 of the axis) —
    # farther apart than either entity is tall.
    assert same_plane(0.34, 0.66) is False


def test_same_plane_symmetric():
    assert same_plane(0.2, 0.3) == same_plane(0.3, 0.2)
