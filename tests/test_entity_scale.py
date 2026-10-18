"""Every entity's hitbox is its base pixel size times ENTITY_SCALE, so
the sprites drawn into those hitboxes all grow or shrink together."""

from game.config import (
    ENTITY_SCALE,
    PLAYER_BASE_SIZE,
    ENEMY_BASE_SIZE,
    SHARD_BASE_RADIUS,
)
from game.simulation.player import Player
from game.simulation.enemy import Enemy
from game.simulation.shard import Shard


def _scaled(size):
    return (size[0] * ENTITY_SCALE, size[1] * ENTITY_SCALE)


def test_player_hitbox_is_its_base_size_scaled():
    assert Player().rect.size == _scaled(PLAYER_BASE_SIZE)


def test_enemy_hitbox_is_its_base_size_scaled():
    assert Enemy("left", 500, 500).rect.size == _scaled(ENEMY_BASE_SIZE)


def test_enemy_loaded_from_dict_has_the_same_scaled_hitbox():
    enemy = Enemy.from_dict({"x": 500, "y": 500, "vx": 2.2, "type": "grunt", "dead": False})
    assert enemy.rect.size == _scaled(ENEMY_BASE_SIZE)


def test_shard_radius_is_its_base_radius_scaled():
    assert Shard(0, 0, angle=0, speed=0).radius == SHARD_BASE_RADIUS * ENTITY_SCALE
