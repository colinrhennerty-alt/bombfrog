"""Tests for the per-frame simulation step that used to live untested
inside main.py's event loop: bomb explosions (fuse and contact-triggered),
enemy/shard collisions, life loss vs. game-over, and spawn timing.
"""

import pygame

from game.config import BOMB_FUSE_MS, MAX_ENEMIES, ENEMY_SPAWN_MS, WORLD_BORDER, BOMB_CONTACT_GRACE_MS
from game.simulation.bomb import Bomb
from game.simulation.enemy import Enemy
from game.simulation.shard import Shard
from game.simulation.world import World

NO_KEYS = {
    pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False,
}


def _place_enemy_at(enemy, x, y):
    enemy.x, enemy.y = x, y
    enemy.rect = enemy.rect.moved_topleft(x, y)


def _new_enemy(x=500, y=500):
    return Enemy("left", x, y)


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
    enemy = _new_enemy()
    enemy.hp = 1
    _place_enemy_at(enemy, 80, 5000)
    world.enemies = [enemy]

    bomb = Bomb(100, 5000)
    bomb.timer = 0  # ready to explode this frame
    bomb.has_shrapnel = False
    world.bombs = [bomb]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.bombs == []
    assert world.enemies == []  # killed by the explosion
    assert world.score == 100 + 1  # kill bonus + this frame's score tick


def test_freshly_spawned_bomb_survives_its_first_tick_even_touching_an_enemy():
    # Reported bug: "I don't see the bomb drop when I am over an enemy."
    # A bomb created via Player.create_bomb() at the jump apex directly
    # above an enemy would previously spawn and contact-explode in the
    # same world.update() call — the bomb never rendered for even one
    # frame. A bomb must survive the tick it's created on regardless of
    # what it's overlapping, then behave normally afterward.
    world = World(now=0)
    enemy = _new_enemy()
    bomb = Bomb(enemy.x, enemy.y)  # spawned already overlapping the enemy
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)
    world.bombs = [bomb]
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)
    assert world.bombs == [bomb]  # still alive after its first tick

    # Contact-triggering stays off for a short grace period after
    # spawning (BOMB_CONTACT_GRACE_MS) so the bomb is actually visible to
    # a player, not just technically present for one imperceptible tick.
    # contact_armed reflects the bomb's armed state *before* each tick's
    # own update, so the grace period must fully elapse in an earlier
    # tick before a later tick's contact-check can see it as armed.
    world.update(NO_KEYS, dt=BOMB_CONTACT_GRACE_MS, now=1016)
    assert world.bombs == [bomb]  # still alive: armed only takes effect next tick

    world.update(NO_KEYS, dt=16, now=1200)
    assert world.bombs == []  # now detonates, same as always


def test_bomb_explodes_on_enemy_contact_even_before_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS  # nowhere near its own fuse
    enemy = _new_enemy()
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)

    world = World(now=0)
    world.bombs = [bomb]
    world.enemies = [enemy]

    # A bomb stays contact-immune for BOMB_CONTACT_GRACE_MS after it's
    # placed (see test_freshly_spawned_bomb_survives_its_first_tick_...).
    # contact_armed reflects the bomb's armed state *before* each tick's
    # own update, so the grace period must fully elapse in an earlier
    # tick before a later tick's contact-check can see it as armed.
    world.update(NO_KEYS, dt=BOMB_CONTACT_GRACE_MS, now=1000)
    world.update(NO_KEYS, dt=1, now=1001)

    assert world.bombs == []  # detonated on contact, not from the fuse


def test_enemy_collision_costs_a_life_and_respawns_without_wiping_score():
    world = World(now=0)
    world.score = 500
    enemy = _new_enemy()
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 2  # actually decremented, not reset back to 3
    assert world.score == 501  # score survives a respawn, plus this frame's +1
    assert world.game_over is False
    assert world.enemies == []  # arena cleared by the respawn


def test_jumping_over_an_enemy_avoids_the_collision():
    # Jumping should let the player dodge an enemy underneath them —
    # on_ground already tracks "airborne for the whole jump arc", reuse
    # it rather than adding new state.
    world = World(now=0)
    world.player.on_ground = False
    world.player.jump_offset = -50  # mid-air, not about to land this frame
    enemy = _new_enemy()
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 3
    assert world.game_over is False
    assert world.enemies == [enemy]  # enemy survives too — no collision happened at all


def test_landing_on_an_enemy_still_costs_a_life():
    # Sanity check alongside the jump-dodge test: grounded collision must
    # still work exactly as before.
    world = World(now=0)
    world.player.on_ground = True
    enemy = _new_enemy()
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 2


def test_jumping_over_shrapnel_avoids_the_collision():
    # Reported bug: bombing an enemy while jumping directly over it spawns
    # death shrapnel right at the player's *hitbox* position (which stays
    # grounded during a jump — jump_offset is purely visual), so the
    # player took an instant, invisible hit with no on-screen feedback
    # even though the sprite was clearly airborne. Jumping should dodge
    # shrapnel exactly the same way it dodges enemies.
    world = World(now=0)
    world.player.on_ground = False
    world.player.jump_offset = -50
    shard = Shard(world.player.rect.centerx, world.player.rect.centery, angle=0, speed=0)
    world.shards = [shard]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 3
    assert world.game_over is False


def test_landing_on_shrapnel_still_costs_a_life():
    world = World(now=0)
    world.player.on_ground = True
    shard = Shard(world.player.rect.centerx, world.player.rect.centery, angle=0, speed=0)
    world.shards = [shard]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.lives == 2


def test_losing_the_last_life_ends_the_game():
    world = World(now=0)
    world.lives = 1
    enemy = _new_enemy()
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert world.game_over is True


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
    world.enemies = [_new_enemy() for _ in range(MAX_ENEMIES)]
    world.update(NO_KEYS, dt=16, now=ENEMY_SPAWN_MS)
    assert len(world.enemies) == MAX_ENEMIES


class _FakeRng:
    """Duck-typed stand-in for the `random` module: returns a fixed,
    caller-chosen side instead of an actual random draw and records what
    World asked of it."""

    def __init__(self, choice_result):
        self.choice_result = choice_result
        self.choice_calls = []

    def choice(self, population):
        self.choice_calls.append(population)
        return self.choice_result


def test_world_uses_injected_rng_to_pick_enemy_spawn_side():
    fake = _FakeRng(choice_result="right")
    world = World(now=0, rng=fake)

    world.update(NO_KEYS, dt=16, now=ENEMY_SPAWN_MS)

    assert len(fake.choice_calls) == 1
    assert fake.choice_calls[0] == ["left", "right"]


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


# --- extracted single-responsibility seams -------------------------------
# These were duplicated (life-loss/reset) or buried inline (the bomb-trigger
# rule) inside the old monolithic update(). Testing them directly is what
# makes the extraction worth doing rather than just internal shuffling.


def test_lose_a_life_respawns_without_wiping_score_or_remaining_lives():
    world = World(now=0)
    world.lives = 3
    world.score = 500
    old_player = world.player
    world.enemies = [_new_enemy()]

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
    assert world._bomb_should_explode(bomb, contact_armed=False) is True


def test_bomb_should_explode_on_enemy_contact_even_with_fuse_unready():
    world = World(now=0)
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = _new_enemy()
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)
    world.enemies = [enemy]
    assert world._bomb_should_explode(bomb, contact_armed=True) is True


def test_bomb_does_not_contact_explode_before_its_first_tick():
    # A bomb that hasn't survived a tick yet (contact_armed=False) must
    # not contact-explode even while overlapping an enemy — see
    # test_freshly_spawned_bomb_survives_its_first_tick_even_touching_an_enemy
    # for the end-to-end version of this via world.update().
    world = World(now=0)
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = _new_enemy()
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)
    world.enemies = [enemy]
    assert world._bomb_should_explode(bomb, contact_armed=False) is False


def test_bomb_should_not_explode_when_fuse_unready_and_no_contact():
    world = World(now=0)
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = _new_enemy()
    _place_enemy_at(enemy, 5000, 5000)  # nowhere near the bomb
    world.enemies = [enemy]
    assert world._bomb_should_explode(bomb, contact_armed=True) is False


# --- debug-mode collision logging ------------------------------------------
# All silent when world.debug is False (the default); with it on, collision
# decisions get logged so issues are visible immediately instead of
# requiring a screenshot and a guessing game.


def test_no_log_output_when_debug_is_off(capsys):
    world = World(now=0)
    enemy = _new_enemy()
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    assert capsys.readouterr().out == ""


def test_logs_enemy_player_collision(capsys):
    world = World(now=0)
    world.debug = True
    enemy = _new_enemy()
    _place_enemy_at(enemy, world.player.x, world.player.y)
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=16, now=1000)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "enemy" in out.lower() and "player" in out.lower()


def test_logs_bomb_contact_trigger(capsys):
    world = World(now=0)
    world.debug = True
    bomb = Bomb(100, 100)
    bomb.timer = BOMB_FUSE_MS
    enemy = _new_enemy()
    _place_enemy_at(enemy, bomb.x - 5, bomb.y - 5)
    world.bombs = [bomb]
    world.enemies = [enemy]

    world.update(NO_KEYS, dt=BOMB_CONTACT_GRACE_MS, now=1000)  # bomb survives the grace period
    capsys.readouterr()  # discard this tick's output
    world.update(NO_KEYS, dt=1, now=1001)

    out = capsys.readouterr().out
    assert "[debug]" in out
    assert "bomb" in out.lower() and "contact" in out.lower()


def test_logs_bomb_killing_an_enemy(capsys):
    world = World(now=0)
    world.debug = True
    enemy = _new_enemy()
    enemy.hp = 1
    _place_enemy_at(enemy, 80, 5000)
    world.enemies = [enemy]

    bomb = Bomb(100, 5000)
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
    enemy = _new_enemy()
    enemy.vx = 0  # stays put, so this frame's enemy.update() doesn't drift it off the shard
    _place_enemy_at(enemy, WORLD_BORDER + 100, WORLD_BORDER + 100)  # outside the stone border
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
