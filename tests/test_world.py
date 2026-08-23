"""Tests for the per-frame simulation step that used to live untested
inside main.py's event loop: bomb explosions (fuse and contact-triggered),
enemy/shard collisions, life loss vs. game-over, and spawn timing.
"""

import pygame

from game.config import GROUND_Y, BOMB_FUSE_MS, MAX_ENEMIES, ENEMY_SPAWN_MS
from game.entities import Bomb, Enemy
from game.world import World

NO_KEYS = {pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False}


def _place_enemy_at(enemy, x, y):
    enemy.x, enemy.y = x, y
    enemy.rect.topleft = (x, y)


def test_world_starts_with_full_lives_and_zero_score():
    world = World(now=0)
    assert world.lives == 3
    assert world.score == 0
    assert world.game_over is False
    assert world.bombs == [] and world.enemies == [] and world.shards == []


def test_bomb_explosion_on_fuse_damages_nearby_enemy_and_scores():
    world = World(now=0)
    # Kept far from the player: the killed enemy's own death shrapnel spawns
    # at its position, and if that's right next to the player it hits back
    # in this same frame, masking the score assertion below with a reset.
    enemy = Enemy("left")
    enemy.hp = 1
    _place_enemy_at(enemy, 80, GROUND_Y - enemy.height)
    world.enemies = [enemy]

    bomb = Bomb(100, GROUND_Y - 16)
    bomb.timer = 0  # ready to explode this frame
    bomb.has_shrapnel = False
    world.bombs = [bomb]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.bombs == []
    assert world.enemies == []  # killed by the explosion
    assert world.score == 100 + 1  # kill bonus + this frame's score tick


def test_bomb_explodes_on_enemy_contact_even_before_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS  # nowhere near its own fuse
    enemy = Enemy("left")
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)

    world = World(now=0)
    world.bombs = [bomb]
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=1, now=1000)

    assert world.bombs == []  # detonated on contact, not from the fuse


def test_enemy_collision_costs_a_life_and_resets_the_round_when_lives_remain():
    world = World(now=0)
    world.score = 500
    enemy = Enemy("left")
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 3  # reset() restores full lives...
    assert world.score == 1  # ...and score, then this frame's +1 still applies
    assert world.game_over is False


def test_losing_the_last_life_ends_the_game():
    world = World(now=0)
    world.lives = 1
    enemy = Enemy("left")
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.game_over is True


def test_update_is_a_noop_once_game_over():
    world = World(now=0)
    world.game_over = True
    world.score = 42
    world.update(NO_KEYS, dt=16, now=1000)
    assert world.score == 42


def test_enemy_spawns_after_the_spawn_interval_elapses():
    world = World(now=0)
    world.update(NO_KEYS, dt=16, now=ENEMY_SPAWN_MS)
    assert len(world.enemies) == 1
    assert world.last_spawn == ENEMY_SPAWN_MS


def test_enemy_does_not_spawn_before_the_interval_elapses():
    world = World(now=0)
    world.update(NO_KEYS, dt=16, now=ENEMY_SPAWN_MS - 1)
    assert len(world.enemies) == 0


def test_enemy_spawn_capped_at_max_enemies():
    world = World(now=0)
    world.enemies = [Enemy("left") for _ in range(MAX_ENEMIES)]
    world.update(NO_KEYS, dt=16, now=ENEMY_SPAWN_MS)
    assert len(world.enemies) == MAX_ENEMIES


def _save_dict(**overrides):
    data = {
        "player": {
            "x": 10, "y": 20, "vx": 0, "vy": 0, "on_ground": True,
            "bombs_left": 1, "pending_bomb": False, "bomb_cooldown": 0,
        },
        "bombs": [],
        "shards": [],
        "enemies": [],
        "score": 55,
        "lives": 2,
        "last_spawn": 999,
    }
    data.update(overrides)
    return data


def test_from_save_data_round_trips_and_starts_fresh_on_game_state():
    loaded = World.from_save_data(_save_dict(), now=0)
    assert loaded.player.x == 10
    assert loaded.player.y == 20
    assert loaded.score == 55
    assert loaded.lives == 2
    assert loaded.last_spawn == 999
    assert loaded.game_over is False
    assert loaded.effects == []


def test_merge_save_data_keeps_current_value_when_missing_from_save():
    world = World(now=0)
    world.score = 77
    data = _save_dict()
    del data["score"]

    world.merge_save_data(data)

    assert world.score == 77  # fell back to the current value
    assert world.last_spawn == 999
