"""Tests for the per-frame simulation step that used to live untested
inside main.py's event loop: bomb explosions (fuse and contact-triggered),
enemy/shard collisions, life loss vs. game-over, and spawn timing.
"""

import pygame

from game.config import GROUND_NEAR_Y, BOMB_FUSE_MS, MAX_ENEMIES, ENEMY_SPAWN_MS, DEPTH_COLLISION_TOLERANCE
from game.entities import Bomb, Enemy, Shard
from game.world import World

NO_KEYS = {
    pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False,
}


def _place_enemy_at(enemy, x, y, depth=None):
    enemy.x, enemy.y = x, y
    if depth is not None:
        enemy.depth = depth
    enemy.rect.topleft = (x, y)


def test_world_starts_with_full_lives_and_zero_score():
    world = World(now=0)
    assert world.lives == 3
    assert world.score == 0
    assert world.game_over is False
    assert world.bombs == [] and world.enemies == [] and world.shards == []


def test_world_debug_starts_off_and_survives_a_respawn():
    world = World(now=0)
    assert world.debug is False

    world.debug = True
    world._respawn(now=0)
    assert world.debug is True  # not a round-specific setting


def test_bomb_explosion_on_fuse_damages_nearby_enemy_and_scores():
    world = World(now=0)
    # Kept far from the player: the killed enemy's own death shrapnel spawns
    # at its position, and if that's right next to the player it hits back
    # in this same frame, masking the score assertion below with a reset.
    enemy = Enemy("left")
    enemy.hp = 1
    _place_enemy_at(enemy, 80, GROUND_NEAR_Y - enemy.height)
    world.enemies = [enemy]

    bomb = Bomb(100, GROUND_NEAR_Y - 16)
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


def test_enemy_collision_costs_a_life_and_respawns_without_wiping_score():
    world = World(now=0)
    world.score = 500
    enemy = Enemy("left")
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=world.player.depth)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 2  # actually decremented, not reset back to 3
    assert world.score == 501  # score survives a respawn, plus this frame's +1
    assert world.game_over is False
    assert world.enemies == []  # arena cleared by the respawn


def test_losing_the_last_life_ends_the_game():
    world = World(now=0)
    world.lives = 1
    enemy = Enemy("left")
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=world.player.depth)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.game_over is True


def test_enemy_in_a_different_z_plane_does_not_cost_a_life():
    # Same x/y overlap as the collision tests above, but the enemy's depth
    # is placed comfortably beyond DEPTH_COLLISION_TOLERANCE from the
    # player's — derived from the constant, not a magic number, so this
    # keeps testing "beyond tolerance" even if the tolerance is retuned.
    world = World(now=0)
    world.player.depth = 0.5
    world.score = 500
    enemy = Enemy("left")
    different_plane_depth = world.player.depth - DEPTH_COLLISION_TOLERANCE - 0.05
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=different_plane_depth)

    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 3  # untouched
    assert world.enemies == [enemy]  # no respawn happened, enemy still there
    assert world.game_over is False


def test_enemy_in_the_same_z_plane_still_costs_a_life():
    # Depth placed comfortably within DEPTH_COLLISION_TOLERANCE of the
    # player's — derived, so this stays meaningful under retuning too.
    world = World(now=0)
    world.player.depth = 0.5
    world.score = 500
    enemy = Enemy("left")
    same_plane_depth = world.player.depth + DEPTH_COLLISION_TOLERANCE - 0.05
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=same_plane_depth)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 2
    assert world.enemies == []


def test_repeated_hits_eventually_end_the_game():
    # Regression test: _lose_a_life used to call reset(), which set lives
    # back to 3 on every non-fatal hit — making lives always == 3 at the
    # moment of collision, so game_over could never actually be reached.
    world = World(now=0)
    for i in range(3):
        world._lose_a_life(now=1000 + i)
    assert world.lives == 0
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
            "x": 10, "y": 20, "vx": 0, "vy": 0, "depth": 0.3, "on_ground": True,
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
    assert loaded.player.depth == 0.3
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


# --- extracted single-responsibility seams -------------------------------
# These were duplicated (life-loss/reset) or buried inline (the bomb-trigger
# rule) inside the old monolithic update(). Testing them directly is what
# makes the extraction worth doing rather than just internal shuffling.


def test_lose_a_life_respawns_without_wiping_score_or_remaining_lives():
    world = World(now=0)
    world.lives = 3
    world.score = 500
    old_player = world.player
    world.enemies = [Enemy("left")]

    world._lose_a_life(now=1234)

    assert world.lives == 2  # actually decremented, not reset back to 3
    assert world.score == 500  # score survives a respawn
    assert world.game_over is False
    assert world.last_spawn == 1234
    assert world.player is not old_player  # fresh player placed back at spawn
    assert world.enemies == []  # arena cleared


def test_lose_a_life_ends_the_game_at_zero_lives():
    world = World(now=0)
    world.lives = 1
    world.score = 500

    world._lose_a_life(now=1234)

    assert world.lives == 0
    assert world.game_over is True
    assert world.score == 500  # no reset once it's game over


def test_bomb_should_explode_when_fuse_is_ready():
    world = World(now=0)
    bomb = Bomb(100, 100)
    bomb.timer = 0
    assert world._bomb_should_explode(bomb) is True


def test_bomb_should_explode_on_enemy_contact_even_with_fuse_unready():
    world = World(now=0)
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = Enemy("left")
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)
    world.enemies = [enemy]
    assert world._bomb_should_explode(bomb) is True


def test_bomb_should_not_explode_when_fuse_unready_and_no_contact():
    world = World(now=0)
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = Enemy("left")
    _place_enemy_at(enemy, 5000, 5000)  # nowhere near the bomb
    world.enemies = [enemy]
    assert world._bomb_should_explode(bomb) is False


# --- debug-mode collision logging ------------------------------------------
# All silent when world.debug is False (the default); with it on, every
# collision decision — including ones *suppressed* by the z-plane check —
# gets logged, so issues like the same_plane bug are visible immediately
# instead of requiring a screenshot and a guessing game.


def test_no_log_output_when_debug_is_off(capsys):
    world = World(now=0)
    enemy = Enemy("left")
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=world.player.depth)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert capsys.readouterr().out == ""


def test_logs_enemy_player_collision_when_same_plane(capsys):
    world = World(now=0)
    world.debug = True
    enemy = Enemy("left")
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=world.player.depth)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "enemy" in out.lower() and "player" in out.lower()


def test_logs_suppressed_collision_when_different_plane(capsys):
    world = World(now=0)
    world.debug = True
    world.player.depth = 0.5
    enemy = Enemy("left")
    different_plane_depth = world.player.depth - DEPTH_COLLISION_TOLERANCE - 0.05
    _place_enemy_at(enemy, world.player.x, world.player.y, depth=different_plane_depth)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "suppressed" in out.lower()
    assert "z-plane" in out.lower() or "plane" in out.lower()


def test_logs_bomb_contact_trigger(capsys):
    world = World(now=0)
    world.debug = True
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = Enemy("left")
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)
    world.bombs = [bomb]
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=1, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "bomb" in out.lower() and "contact" in out.lower()


def test_logs_bomb_killing_an_enemy(capsys):
    world = World(now=0)
    world.debug = True
    enemy = Enemy("left")
    enemy.hp = 1
    _place_enemy_at(enemy, 80, GROUND_NEAR_Y - enemy.height)
    world.enemies = [enemy]

    bomb = Bomb(100, GROUND_NEAR_Y - 16)
    bomb.timer = 0
    bomb.has_shrapnel = False
    world.bombs = [bomb]

    world.update(NO_KEYS, dt=16, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "bomb" in out.lower() and "kill" in out.lower()


def test_logs_shard_hitting_an_enemy(capsys):
    world = World(now=0)
    world.debug = True
    enemy = Enemy("left")
    enemy.vx = 0  # stays put, so this frame's enemy.update() doesn't drift it off the shard
    _place_enemy_at(enemy, 100, 100, depth=0.5)  # fixed depth: deterministic size/scale
    enemy._sync_rect()  # matches what enemy.update() will do, so the shard lands exactly on it
    shard = Shard(enemy.rect.centerx, enemy.rect.centery, angle=0, speed=0)
    world.enemies = [enemy]
    world.shards = [shard]

    world.update(NO_KEYS, dt=1, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "shard" in out.lower() and "enemy" in out.lower()


def test_logs_shard_hitting_the_player(capsys):
    world = World(now=0)
    world.debug = True
    shard = Shard(world.player.rect.centerx, world.player.rect.centery, angle=0, speed=0)
    world.shards = [shard]

    world.update(NO_KEYS, dt=1, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "shard" in out.lower() and "player" in out.lower()
