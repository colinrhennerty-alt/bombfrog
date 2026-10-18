"""Enemies are sized relative to the frog: each type's height is the
frog's height times its EnemyType.height_vs_frog, and its width follows
its critter art's proportions so the sprite is never stretched."""

import dataclasses

import pytest

from game.simulation.enemy import Enemy
from game.simulation.enemy_types import ENEMY_TYPES, HEIGHT_VS_FROG_RANGE
from game.simulation.player import Player

EXPECTED_HEIGHT_VS_FROG = {"grunt": 1.25, "heavy": 1.75, "elite": 2.5}


def _enemy_of_type(enemy_type):
    return Enemy.from_dict({"x": 500, "y": 500, "vx": 2.2, "type": enemy_type, "dead": False})


def test_each_type_has_its_chosen_height_relative_to_the_frog():
    for name, enemy_type in ENEMY_TYPES.items():
        assert enemy_type.height_vs_frog == EXPECTED_HEIGHT_VS_FROG[name]


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_enemy_height_is_the_frogs_height_times_its_ratio(enemy_type):
    expected = round(Player().height * ENEMY_TYPES[enemy_type].height_vs_frog)
    assert _enemy_of_type(enemy_type).rect.size[1] == expected


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_enemy_width_follows_its_art_proportions(enemy_type):
    enemy = _enemy_of_type(enemy_type)
    assert enemy.rect.size[0] == round(enemy.height * ENEMY_TYPES[enemy_type].art_aspect)


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_a_freshly_spawned_enemy_gets_its_types_size(enemy_type):
    class _AlwaysPicks:
        def choices(self, population, weights):
            return [enemy_type]

        def uniform(self, a, b):
            return 0

    spawned = Enemy("left", 500, 500, rng=_AlwaysPicks())
    assert spawned.rect.size == _enemy_of_type(enemy_type).rect.size


def test_the_frog_is_smaller_than_the_stag():
    frog = Player()
    stag = _enemy_of_type("elite")
    assert frog.height < stag.height
    assert frog.width * frog.height < stag.width * stag.height


def test_bigger_enemy_tiers_are_taller():
    heights = [_enemy_of_type(t).height for t in ("grunt", "heavy", "elite")]
    assert heights == sorted(heights) and len(set(heights)) == 3


@pytest.mark.parametrize("ratio_offset", [-0.01, 0.01])
def test_a_type_sized_outside_the_reasonable_range_is_rejected(ratio_offset):
    low, high = HEIGHT_VS_FROG_RANGE
    out_of_range = low + ratio_offset if ratio_offset < 0 else high + ratio_offset
    with pytest.raises(ValueError):
        dataclasses.replace(ENEMY_TYPES["grunt"], height_vs_frog=out_of_range)


@pytest.mark.parametrize("edge", [0, 1])
def test_a_type_sized_at_the_edge_of_the_range_is_allowed(edge):
    dataclasses.replace(ENEMY_TYPES["grunt"], height_vs_frog=HEIGHT_VS_FROG_RANGE[edge])
