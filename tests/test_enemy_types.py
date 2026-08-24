import math

from game.simulation.enemy_types import ENEMY_TYPES

# Regression pins matching today's hardcoded values, so the registry can't
# silently drift from the original game balance during refactors.
EXPECTED_MAX_HP = {"grunt": 1, "heavy": 2, "elite": 3}
EXPECTED_SPAWN_WEIGHT = {"grunt": 0.55, "heavy": 0.30, "elite": 0.15}
EXPECTED_SHRAPNEL_COUNT = {"grunt": 6, "heavy": 5, "elite": 8}


def test_registry_has_exactly_the_expected_types():
    assert set(ENEMY_TYPES.keys()) == set(EXPECTED_MAX_HP.keys())


def test_spawn_weights_sum_to_one():
    total = sum(t.spawn_weight for t in ENEMY_TYPES.values())
    assert math.isclose(total, 1.0)


def test_every_enemy_type_matches_known_hp_weight_and_shrapnel_count():
    for name, enemy_type in ENEMY_TYPES.items():
        assert enemy_type.name == name
        assert enemy_type.max_hp == EXPECTED_MAX_HP[name]
        assert math.isclose(enemy_type.spawn_weight, EXPECTED_SPAWN_WEIGHT[name])

        shrapnel = enemy_type.shrapnel_pattern(direction=0.0)
        assert len(shrapnel) == EXPECTED_SHRAPNEL_COUNT[name]
        for angle, speed_multiplier, color in shrapnel:
            assert isinstance(angle, float)
            assert speed_multiplier > 0
            assert color is None or len(color) == 3


def test_heavy_shrapnel_cone_points_toward_facing_direction():
    heavy = ENEMY_TYPES["heavy"]
    forward = [angle for angle, _, _ in heavy.shrapnel_pattern(direction=0.0)]
    backward = [angle for angle, _, _ in heavy.shrapnel_pattern(direction=math.pi)]

    assert min(abs(a) for a in forward) < min(abs(a) for a in backward)
