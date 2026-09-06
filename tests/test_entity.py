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
