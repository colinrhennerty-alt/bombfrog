from game.config import BOMB_FUSE_MS, BOMB_FALL_SPEED
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
    original = Bomb(50, 60)
    original.timer = 321
    original.has_shrapnel = True
    restored = Bomb.from_dict(
        {
            "x": original.x, "y": original.y, "timer": original.timer,
            "has_shrapnel": original.has_shrapnel,
        }
    )
    assert restored.x == original.x
    assert restored.y == original.y
    assert restored.timer == original.timer
    assert restored.has_shrapnel is True


def test_bomb_defaults_fall_offset_to_zero():
    assert Bomb(100, 100).fall_offset == 0


def test_bomb_accepts_fall_offset_at_construction():
    assert Bomb(100, 100, fall_offset=-80).fall_offset == -80


def test_bomb_fall_offset_eases_toward_zero_over_a_tick():
    bomb = Bomb(100, 100, fall_offset=-80)
    bomb.update(dt=16)
    assert bomb.fall_offset == -80 + BOMB_FALL_SPEED
    assert -80 < bomb.fall_offset < 0


def test_bomb_fall_offset_reaches_exactly_zero_without_overshoot():
    bomb = Bomb(100, 100, fall_offset=-5)
    bomb.update(dt=16)
    assert bomb.fall_offset == 0


def test_bomb_fall_offset_never_overshoots_past_zero_over_many_ticks():
    bomb = Bomb(100, 100, fall_offset=-80)
    for _ in range(20):
        bomb.update(dt=16)
        assert bomb.fall_offset <= 0
    assert bomb.fall_offset == 0


def test_bomb_world_position_and_rect_unaffected_by_fall_offset():
    bomb = Bomb(100, 100, fall_offset=-80)
    for _ in range(5):
        bomb.update(dt=16)
        assert bomb.x == 100
        assert bomb.y == 100
        assert bomb.rect.center == (100, 100)


def test_bomb_zero_fall_offset_stays_zero():
    bomb = Bomb(100, 100)
    bomb.update(dt=16)
    assert bomb.fall_offset == 0


def test_bomb_from_dict_defaults_fall_offset_to_zero_when_missing():
    restored = Bomb.from_dict({"x": 10, "y": 20, "timer": 500, "has_shrapnel": False})
    assert restored.fall_offset == 0


def test_bomb_from_dict_round_trips_fall_offset_when_present():
    original = Bomb(50, 60, fall_offset=-40)
    restored = Bomb.from_dict(
        {
            "x": original.x, "y": original.y, "timer": original.timer,
            "has_shrapnel": original.has_shrapnel, "fall_offset": original.fall_offset,
        }
    )
    assert restored.fall_offset == -40
