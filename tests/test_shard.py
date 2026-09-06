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


def test_shard_shadow_anchor_is_its_center_not_its_feet():
    # Shard is circular (no "feet") — its shadow belongs at rect.center,
    # matching the rendering contract every drawable entity exposes
    # (see rendering.draw_scene).
    shard = Shard(100, 100, angle=0, speed=0)
    assert shard.shadow_anchor == shard.rect.center
