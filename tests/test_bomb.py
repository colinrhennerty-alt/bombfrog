from game.config import BOMB_FUSE_MS, BOMB_FALL_SPEED, BOMB_CONTACT_GRACE_MS
from game.simulation.bomb import Bomb


def test_bomb_starts_unarmed():
    # A freshly spawned bomb must stay visible for a short, actually
    # perceptible grace period before it can contact-explode — a single
    # simulation tick (16ms) technically satisfies "exists for a frame"
    # but is imperceptible to a human eye (reported: "I only get a split
    # second of seeing the bomb when over an enemy").
    bomb = Bomb(100, 100)
    assert bomb.armed is False


def test_bomb_stays_unarmed_for_a_single_tick():
    bomb = Bomb(100, 100)
    bomb.update(dt=16)
    assert bomb.armed is False


def test_bomb_becomes_armed_once_the_contact_grace_period_elapses():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_CONTACT_GRACE_MS)
    assert bomb.armed is True


def test_bomb_loaded_from_a_save_is_already_armed():
    # A bomb round-tripped through save/load already existed in the world
    # for at least one tick before saving — it must not get a fresh
    # contact-immunity grace period every time a save is loaded.
    bomb = Bomb.from_dict({"x": 100, "y": 100, "timer": 500})
    assert bomb.armed is True


def test_bomb_not_ready_before_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_FUSE_MS - 1)
    assert bomb.is_ready() is False


def test_bomb_ready_after_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_FUSE_MS)
    assert bomb.is_ready() is True


def test_bomb_not_ready_even_after_fuse_expires_while_still_falling():
    # Reported: "the bomb shouldn't explode until it hits the ground or
    # an enemy." A bomb dropped from a big jump can still be mid-air
    # (fall_offset != 0) when its fuse timer alone would say it's ready —
    # is_ready() must also require the bomb to have actually landed.
    # BOMB_FALL_SPEED * (BOMB_FUSE_MS / 16) is the most a fall_offset can
    # decay by the time the fuse expires — start further than that so it
    # provably hasn't landed yet.
    max_decay_over_fuse = BOMB_FALL_SPEED * (BOMB_FUSE_MS / 16)
    bomb = Bomb(100, 100, fall_offset=-(max_decay_over_fuse * 2))
    bomb.update(dt=BOMB_FUSE_MS)
    assert bomb.fall_offset != 0  # sanity: still airborne after this tick
    assert bomb.is_ready() is False


def test_bomb_ready_once_it_lands_even_if_the_fuse_already_expired():
    bomb = Bomb(100, 100, fall_offset=-40)  # small enough to land within one tick
    bomb.update(dt=BOMB_FUSE_MS)
    assert bomb.fall_offset == 0  # sanity: landed this tick
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


class _FakeRng:
    """Duck-typed stand-in for the `random` module: records exactly what
    Bomb asked of it and returns a fixed, caller-chosen value instead of
    an actual random draw."""

    def __init__(self, random_value):
        self.random_value = random_value
        self.random_calls = 0

    def random(self):
        self.random_calls += 1
        return self.random_value


def test_bomb_uses_injected_rng_to_decide_shrapnel():
    below_threshold = _FakeRng(0.04)  # has_shrapnel triggers at random() < 0.05
    bomb = Bomb(100, 100, rng=below_threshold)
    assert bomb.has_shrapnel is True
    assert below_threshold.random_calls == 1


def test_bomb_injected_rng_can_suppress_shrapnel_deterministically():
    above_threshold = _FakeRng(0.5)
    bomb = Bomb(100, 100, rng=above_threshold)
    assert bomb.has_shrapnel is False
