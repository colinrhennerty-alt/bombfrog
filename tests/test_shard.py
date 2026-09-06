from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
from game.simulation.shard import Shard


def test_shard_is_alive_within_bounds_and_lifetime():
    shard = Shard(WIDTH / 2, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is True


def test_shard_is_alive_beyond_the_viewport_but_still_in_the_world():
    shard = Shard(WIDTH * 2, HEIGHT * 2, angle=0, speed=0)
    assert shard.is_alive() is True


def test_shard_dies_when_lifetime_expires():
    shard = Shard(WIDTH / 2, HEIGHT / 2, angle=0, speed=0)
    shard.life = 0
    assert shard.is_alive() is False


def test_shard_dies_when_it_leaves_the_world():
    shard = Shard(-10, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is False
    shard = Shard(WORLD_WIDTH + 10, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is False
