from game.config import BOMB_FUSE_MS
from game.simulation.depth import scale_for_depth
from game.simulation.bomb import Bomb


def test_bomb_not_ready_before_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_FUSE_MS - 1)
    assert bomb.is_ready() is False


def test_bomb_ready_after_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_FUSE_MS)
    assert bomb.is_ready() is True


def test_bomb_from_dict_round_trips_fields():
    original = Bomb(50, 60, depth=0.3)
    original.timer = 321
    original.has_shrapnel = True
    restored = Bomb.from_dict(
        {
            "x": original.x, "y": original.y, "timer": original.timer,
            "has_shrapnel": original.has_shrapnel, "depth": original.depth,
        }
    )
    assert restored.x == original.x
    assert restored.y == original.y
    assert restored.timer == original.timer
    assert restored.has_shrapnel is True
    assert restored.depth == 0.3


def test_bomb_defaults_to_near_depth_and_full_scale():
    bomb = Bomb(50, 60)
    assert bomb.depth == 1.0
    assert bomb.scale == scale_for_depth(1.0)


def test_bomb_from_dict_defaults_missing_depth_to_one():
    data = {"x": 1, "y": 2, "timer": 100}
    bomb = Bomb.from_dict(data)
    assert bomb.depth == 1.0
