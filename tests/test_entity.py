"""Every drawable/simulated entity duck-types the same shape (x, y, rect,
shadow_anchor) so game.rendering.renderer can treat them polymorphically.
Pins that contract explicitly via the Entity Protocol, rather than only
being implicitly relied on by renderer's getattr fallbacks.
"""

from game.simulation.entity import Entity
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy


def test_player_satisfies_the_entity_protocol():
    assert isinstance(Player(), Entity)


def test_bomb_satisfies_the_entity_protocol():
    assert isinstance(Bomb(100, 100), Entity)


def test_shard_satisfies_the_entity_protocol():
    assert isinstance(Shard(100, 100, angle=0, speed=0), Entity)


def test_enemy_satisfies_the_entity_protocol():
    assert isinstance(Enemy("left", 500, 500), Entity)


def test_player_shadow_radius_is_its_width():
    player = Player()
    assert player.shadow_radius == player.width


def test_enemy_shadow_radius_is_its_width():
    enemy = Enemy("left", 500, 500)
    assert enemy.shadow_radius == enemy.width


def test_bomb_shadow_radius_is_its_radius():
    bomb = Bomb(100, 100)
    assert bomb.shadow_radius == bomb.radius


def test_shard_shadow_radius_is_its_radius():
    shard = Shard(100, 100, angle=0, speed=0)
    assert shard.shadow_radius == shard.radius


def test_player_shadow_height_offset_is_its_jump_offset():
    player = Player()
    player.jump_offset = -42
    assert player.shadow_height_offset == -42


def test_bomb_shadow_height_offset_is_its_fall_offset():
    bomb = Bomb(100, 100, fall_offset=-17)
    assert bomb.shadow_height_offset == -17


def test_enemy_shadow_height_offset_is_zero_grounded_and_never_airborne():
    enemy = Enemy("left", 500, 500)
    assert enemy.shadow_height_offset == 0


def test_shard_shadow_height_offset_is_zero_grounded_and_never_airborne():
    shard = Shard(100, 100, angle=0, speed=0)
    assert shard.shadow_height_offset == 0
