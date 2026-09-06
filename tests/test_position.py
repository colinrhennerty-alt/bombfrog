from game.simulation.position import Position


def test_clamped_within_bounds_is_unchanged():
    pos = Position(5, 5)
    assert pos.clamped(0, 10, 0, 10) == Position(5, 5)


def test_clamped_clamps_x_low():
    pos = Position(-5, 5)
    assert pos.clamped(0, 10, 0, 10) == Position(0, 5)


def test_clamped_clamps_x_high():
    pos = Position(15, 5)
    assert pos.clamped(0, 10, 0, 10) == Position(10, 5)


def test_clamped_clamps_y_low():
    pos = Position(5, -5)
    assert pos.clamped(0, 10, 0, 10) == Position(5, 0)


def test_clamped_clamps_y_high():
    pos = Position(5, 15)
    assert pos.clamped(0, 10, 0, 10) == Position(5, 10)


def test_position_is_frozen():
    pos = Position(1, 2)
    try:
        pos.x = 5
        assert False, "Position should be immutable"
    except AttributeError:
        pass
