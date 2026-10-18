import math
import pytest
import random

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, ENEMY_ANIM_MS
from game.simulation.camera import Camera
from game.simulation.enemy import Enemy
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.rect import _round_half_away_from_zero


def test_enemy_takes_damage_and_dies_at_zero_hp():
    enemy = Enemy("left", 500, 500)
    enemy.hp = 2
    enemy.take_damage()
    assert enemy.hp == 1
    assert enemy.dead is False
    enemy.take_damage()
    assert enemy.hp == 0
    assert enemy.dead is True


def test_enemy_bounces_off_the_stone_border():
    # Same inset boundary as the player — enemies bounce off the border
    # zone, not the raw world edge, so they never visually clip into it.
    enemy = Enemy("left", 500, 500)
    enemy.x = WORLD_BORDER
    enemy.vx = -3
    enemy.update(dt=16)
    assert enemy.x == WORLD_BORDER
    assert enemy.vx == 3


def test_enemy_bounces_off_the_far_stone_border():
    enemy = Enemy("left", 500, 500)
    enemy.x = WORLD_WIDTH - WORLD_BORDER - enemy.width
    enemy.vx = 3
    enemy.update(dt=16)
    assert enemy.x == WORLD_WIDTH - WORLD_BORDER - enemy.width
    assert enemy.vx == -3


def test_enemy_spawns_clamped_within_the_stone_border():
    for _ in range(20):
        enemy = Enemy("left", 500, 500)
        assert WORLD_BORDER <= enemy.x <= WORLD_WIDTH - WORLD_BORDER - enemy.width
        assert WORLD_BORDER <= enemy.y <= WORLD_HEIGHT - WORLD_BORDER - enemy.height


def test_enemy_spawns_off_screen_near_left_world_edge():
    # Player near the left world edge: the camera clamps to x=0, so the
    # visible viewport is [0, WIDTH]. A "left" spawn must land outside
    # that viewport, not get clamped back onto the visible screen.
    player_x, player_y = 50, 500
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.snap_to(player_x, player_y)

    enemy = Enemy("left", player_x, player_y, camera=camera)

    assert enemy.x + enemy.width <= camera.x or enemy.x >= camera.x + camera.viewport_width


def test_enemy_spawns_off_screen_near_right_world_edge():
    player_x, player_y = WORLD_WIDTH - 50, 500
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.snap_to(player_x, player_y)

    enemy = Enemy("right", player_x, player_y, camera=camera)

    assert enemy.x + enemy.width <= camera.x or enemy.x >= camera.x + camera.viewport_width


def _expected_midbottom(enemy):
    # Rect anchors like pygame.Rect: half away from zero, not Python's
    # banker's round() — they differ exactly at .5, which odd widths hit.
    return (
        _round_half_away_from_zero(enemy.x + enemy.width / 2),
        _round_half_away_from_zero(enemy.y + enemy.height),
    )


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_enemy_rect_matches_fixed_size(enemy_type):
    enemy = Enemy.from_dict({"x": 1371, "y": 641, "vx": 2.2, "type": enemy_type, "dead": False})
    assert enemy.rect.size == (enemy.width, enemy.height)
    assert enemy.rect.midbottom == _expected_midbottom(enemy)


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_enemy_rect_moves_after_update(enemy_type):
    enemy = Enemy.from_dict({"x": 1371, "y": 641, "vx": 3, "type": enemy_type, "dead": False})
    enemy.update(dt=16)
    assert enemy.rect.midbottom == _expected_midbottom(enemy)


def test_enemy_killed_by_explosion_within_range():
    enemy = Enemy("left", 500, 500)
    enemy.x = 100
    origin_x, origin_y = enemy.rect.centerx, enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is True


def test_enemy_not_killed_by_distant_explosion():
    enemy = Enemy("left", 500, 500)
    enemy.x = 100
    origin_x = enemy.rect.centerx + 1000
    origin_y = enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is False


def test_enemy_from_dict_round_trips_position():
    enemy = Enemy("left", 500, 500)
    restored = Enemy.from_dict(
        {
            "x": enemy.x, "y": enemy.y, "vx": enemy.vx, "type": enemy.type,
            "dead": enemy.dead,
        }
    )
    assert restored.x == enemy.x
    assert restored.y == enemy.y


def test_death_shrapnel_count_matches_enemy_type():
    enemy = Enemy("left", 500, 500)

    enemy.type = "grunt"
    assert len(enemy.get_death_shrapnel()) == 6

    enemy.type = "heavy"
    assert len(enemy.get_death_shrapnel()) == 5

    enemy.type = "elite"
    assert len(enemy.get_death_shrapnel()) == 8


class _FakeRng:
    """Duck-typed stand-in for the `random` module: returns fixed,
    caller-chosen values for the exact calls Enemy makes instead of an
    actual random draw, and records how each was called."""

    def __init__(self, choice_result, uniform_result):
        self.choice_result = choice_result
        self.uniform_result = uniform_result
        self.choices_calls = []
        self.uniform_calls = []

    def choices(self, population, weights):
        self.choices_calls.append((population, weights))
        return [self.choice_result]

    def uniform(self, low, high):
        self.uniform_calls.append((low, high))
        return self.uniform_result


def test_enemy_uses_injected_rng_to_pick_type_and_spawn_offset():
    fake = _FakeRng(choice_result="elite", uniform_result=0)
    enemy = Enemy("left", 500, 500, rng=fake)

    assert enemy.type == "elite"
    assert len(fake.choices_calls) == 1
    assert len(fake.uniform_calls) == 1


def test_enemy_injected_rng_controls_spawn_y_offset_deterministically():
    fake = _FakeRng(choice_result="grunt", uniform_result=37)
    enemy = Enemy("left", 500, 500, rng=fake)

    assert enemy.y == 500 + 37


def test_enemy_shadow_anchor_is_its_feet_not_its_topleft():
    # Enemy stands upright (a rect entity, not circular) — its shadow
    # belongs at rect.midbottom (feet), matching the rendering contract
    # every drawable entity exposes (see game.rendering.entities.draw_scene).
    enemy = Enemy("left", 500, 500)
    assert enemy.shadow_anchor == enemy.rect.midbottom


def test_enemy_from_dict_does_not_invoke_randomness():
    # from_dict fully determines every field from the saved data — it
    # must not run the randomized spawn constructor path (rng.choices /
    # rng.uniform) just to immediately overwrite the result.
    class _ExplodingRng:
        def choices(self, *a, **k):
            raise AssertionError("from_dict must not roll a random enemy type")

        def uniform(self, *a, **k):
            raise AssertionError("from_dict must not roll a random spawn offset")

    original_random = random.choices, random.uniform
    random.choices, random.uniform = _ExplodingRng().choices, _ExplodingRng().uniform
    try:
        Enemy.from_dict(
            {"x": 111, "y": 222, "vx": -2.2, "type": "grunt", "dead": False, "hp": 1}
        )
    finally:
        random.choices, random.uniform = original_random


def test_enemy_to_dict_round_trips_through_from_dict():
    original = Enemy("left", 500, 500)
    original.x, original.y, original.vx = 111, 222, -2.2
    original.hp = 2

    restored = Enemy.from_dict(original.to_dict())

    assert restored.x == original.x
    assert restored.y == original.y
    assert restored.vx == original.vx
    assert restored.type == original.type
    assert restored.dead == original.dead
    assert restored.hp == original.hp


def test_enemy_animation_advances_one_frame_per_enemy_anim_ms():
    enemy = Enemy("left", 500, 500, rng=random.Random(0))
    enemy.vx = 2.2
    assert enemy.anim_index == 0
    enemy.update(dt=ENEMY_ANIM_MS)
    assert enemy.anim_index == 1
    enemy.update(dt=ENEMY_ANIM_MS - 1)
    assert enemy.anim_index == 1


def test_enemy_loaded_from_dict_starts_at_animation_frame_zero_and_can_update():
    enemy = Enemy.from_dict({"x": 500, "y": 500, "vx": 2.2, "type": "grunt", "dead": False})
    assert enemy.anim_index == 0
    enemy.update(dt=ENEMY_ANIM_MS)
    assert enemy.anim_index == 1


# --- following the frog ----------------------------------------------------

from game.config import ENEMY_SPEED, ENEMY_NOTICE_RADIUS, ENEMY_GIVE_UP_RADIUS


class StubRng:
    """random()-only rng that always returns `value` and counts calls."""

    def __init__(self, value):
        self.value = value
        self.calls = 0

    def random(self):
        self.calls += 1
        return self.value


def _wandering_enemy(rng, vx=-ENEMY_SPEED):
    enemy = Enemy("left", WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
    enemy.rng = rng
    enemy.x = WORLD_WIDTH / 2
    enemy.y = WORLD_HEIGHT / 2
    enemy.vx = vx
    enemy._sync_rect()
    return enemy


def _target_at_distance(enemy, distance):
    """A point straight below the enemy's center, `distance` away."""
    return enemy.rect.centerx, enemy.rect.centery + distance


def _chance(enemy):
    return ENEMY_TYPES[enemy.type].follow_chance


def test_enemy_does_not_roll_while_the_frog_is_out_of_notice_range():
    rng = StubRng(0.0)
    enemy = _wandering_enemy(rng)
    y_before = enemy.y
    enemy.update(dt=16, target=_target_at_distance(enemy, ENEMY_NOTICE_RADIUS + 50))
    assert rng.calls == 0
    assert enemy.following is False
    assert enemy.y == y_before


def test_enemy_that_wins_its_roll_moves_toward_the_frog_at_walking_speed():
    rng = StubRng(0.0)
    enemy = _wandering_enemy(rng)
    target = _target_at_distance(enemy, ENEMY_NOTICE_RADIUS - 10)
    x_before, y_before = enemy.x, enemy.y
    enemy.update(dt=16, target=target)
    assert enemy.following is True
    assert math.hypot(enemy.x - x_before, enemy.y - y_before) == pytest.approx(ENEMY_SPEED)
    assert enemy.y > y_before  # target is straight below


def test_enemy_that_loses_its_roll_never_rolls_again():
    rng = StubRng(0.999)
    enemy = _wandering_enemy(rng)
    target = _target_at_distance(enemy, ENEMY_NOTICE_RADIUS - 10)
    for _ in range(5):
        enemy.update(dt=16, target=target)
    assert rng.calls == 1
    assert enemy.following is False
    assert enemy.vy == 0


def test_follow_roll_uses_the_types_follow_chance():
    for name, enemy_type in ENEMY_TYPES.items():
        if not 0 < enemy_type.follow_chance < 1:
            continue
        just_under = _wandering_enemy(StubRng(enemy_type.follow_chance - 0.01))
        just_under.type = name
        just_under.update(dt=16, target=_target_at_distance(just_under, 10))
        just_over = _wandering_enemy(StubRng(enemy_type.follow_chance + 0.01))
        just_over.type = name
        just_over.update(dt=16, target=_target_at_distance(just_over, 10))
        assert just_under.following is True
        assert just_over.following is False


def test_follower_gives_up_when_the_frog_gets_far_away_and_never_rerolls():
    rng = StubRng(0.0)
    enemy = _wandering_enemy(rng, vx=ENEMY_SPEED)
    enemy.update(dt=16, target=(enemy.rect.centerx + 50, enemy.rect.centery))
    assert enemy.following is True

    enemy.update(dt=16, target=_target_at_distance(enemy, ENEMY_GIVE_UP_RADIUS + 50))
    assert enemy.following is False
    assert enemy.vy == 0
    assert abs(enemy.vx) == pytest.approx(ENEMY_SPEED)

    enemy.update(dt=16, target=_target_at_distance(enemy, 10))
    assert enemy.following is False
    assert rng.calls == 1


def test_give_up_radius_is_beyond_notice_radius():
    assert ENEMY_GIVE_UP_RADIUS > ENEMY_NOTICE_RADIUS


def test_follower_stays_inside_the_stone_border_vertically():
    enemy = _wandering_enemy(StubRng(0.0))
    enemy.y = WORLD_BORDER
    enemy._sync_rect()
    enemy.update(dt=16, target=(enemy.rect.centerx, enemy.rect.centery - 100))
    assert enemy.following is True
    assert enemy.y == WORLD_BORDER


def test_enemy_from_dict_without_follow_fields_still_loads_as_wanderer():
    data = {"x": 300, "y": 400, "vx": -2.2, "type": "grunt", "dead": False, "hp": 1}
    enemy = Enemy.from_dict(data)
    assert enemy.following is False
    assert enemy.follow_rolled is False
    assert enemy.vy == 0


def test_enemy_follow_state_round_trips_through_dict():
    enemy = _wandering_enemy(StubRng(0.0))
    enemy.update(dt=16, target=_target_at_distance(enemy, 10))
    restored = Enemy.from_dict(enemy.to_dict())
    assert restored.following is True
    assert restored.follow_rolled is True
    assert restored.vy == pytest.approx(enemy.vy)
