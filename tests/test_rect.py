from game.simulation.rect import Rect


def test_from_midbottom_anchors_at_bottom_center():
    rect = Rect.from_midbottom(mid_x=100, bottom_y=200, width=40, height=60)
    assert rect.x == 80
    assert rect.y == 140
    assert rect.midbottom == (100, 200)


def test_coordinates_truncate_to_int_on_direct_construction():
    """pygame.Rect(x, y, w, h) truncates toward zero on direct
    construction (1.9 -> 1) — different from its property setters, which
    round instead (see test_from_midbottom_rounds_half_away_from_zero)."""
    rect = Rect(1.9, 2.9, 3.9, 4.9)
    assert (rect.x, rect.y, rect.width, rect.height) == (1, 2, 3, 4)


def test_from_midbottom_rounds_half_away_from_zero():
    """pygame.Rect's .midbottom = (...) setter rounds the assigned point
    (half away from zero, not Python's banker's rounding) before deriving
    topleft from it — verified empirically against pygame.Rect."""
    rect = Rect.from_midbottom(mid_x=2.5, bottom_y=-2.5, width=10, height=10)
    assert rect.midbottom == (3, -3)


def test_from_center_anchors_at_center():
    rect = Rect.from_center(center_x=100, center_y=200, width=40, height=60)
    assert rect.center == (100, 200)
    assert rect.centerx == 100
    assert rect.centery == 200


def test_size_returns_width_height_tuple():
    rect = Rect(0, 0, 40, 60)
    assert rect.size == (40, 60)


def test_recentered_returns_new_rect_same_size():
    rect = Rect(0, 0, 40, 60)
    moved = rect.recentered(100, 200)
    assert moved.center == (100, 200)
    assert moved.size == rect.size
    assert rect.center == (20, 30)  # original unchanged (frozen)


def test_moved_topleft_returns_new_rect_same_size():
    rect = Rect(0, 0, 40, 60)
    moved = rect.moved_topleft(10, 20)
    assert (moved.x, moved.y) == (10, 20)
    assert moved.size == rect.size


def test_colliderect_true_when_overlapping():
    a = Rect(0, 0, 10, 10)
    b = Rect(5, 5, 10, 10)
    assert a.colliderect(b)
    assert b.colliderect(a)


def test_colliderect_false_when_separated():
    a = Rect(0, 0, 10, 10)
    b = Rect(20, 20, 10, 10)
    assert not a.colliderect(b)


def test_colliderect_false_when_only_touching_edges():
    a = Rect(0, 0, 10, 10)
    b = Rect(10, 0, 10, 10)
    assert not a.colliderect(b)


def test_rect_is_frozen():
    rect = Rect(0, 0, 10, 10)
    try:
        rect.x = 5
        assert False, "Rect should be immutable"
    except AttributeError:
        pass
