from game.config import WIDTH, HEIGHT
from game.simulation.shard import Shard


def test_shard_is_alive_within_bounds_and_lifetime():
    shard = Shard(WIDTH / 2, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is True


def test_shard_dies_when_lifetime_expires():
    shard = Shard(WIDTH / 2, HEIGHT / 2, angle=0, speed=0)
    shard.life = 0
    assert shard.is_alive() is False


def test_shard_dies_when_it_leaves_the_screen():
    shard = Shard(-10, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is False
