"""Owns one round's simulation state and advances it frame by frame.

This is the logic that used to live inline inside main.py's event loop,
where it had zero test coverage. `World.update()` is the pure-ish
"given input, advance by dt" step; main.py stays responsible for input
polling, the menu, and handing frames to game.rendering.

Session-level state that outlives any single round — the high score —
intentionally is NOT stored here; it belongs to the caller, same as it
was a variable in run_game() that start_new_game() never touched.
"""

import math
import random

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, MAX_ENEMIES, ENEMY_SPAWN_MS, SHARD_SPEED, BOMB_LIMIT
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy
from game.simulation.explosion_effect import ExplosionEffect
from game.simulation.camera import Camera
from game.simulation import debug_log


def _load_bombs_shards_enemies(data):
    bombs = [Bomb.from_dict(b) for b in data["bombs"]]
    shards = [Shard.from_dict(s) for s in data["shards"]]
    enemies = [Enemy.from_dict(e) for e in data["enemies"]]
    return bombs, shards, enemies


class World:
    def __init__(self, now=0):
        self.debug = False
        self.camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
        self.reset(now)

    def reset(self, now=0):
        """Start a brand new round: clears the arena and zeroes score/lives."""
        self._respawn(now)
        self.score = 0
        self.lives = 3

    def _respawn(self, now=0):
        """Clear the arena and place a fresh player, leaving score/lives as-is."""
        self.player = Player()
        self.bombs = []
        self.shards = []
        self.enemies = []
        self.effects = []
        self.game_over = False
        self.last_spawn = now
        self.camera.follow(self.player.centerx, self.player.centery)

    @classmethod
    def from_save_data(cls, data, now=0):
        """Build a fresh World from a save dict (the menu's "Load Game")."""
        world = cls.__new__(cls)
        world.debug = False
        world.camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
        world.player = Player.from_dict(data["player"])
        world.bombs, world.shards, world.enemies = _load_bombs_shards_enemies(data)
        world.score = data.get("score", 0)
        world.lives = data.get("lives", 3)
        world.last_spawn = data.get("last_spawn", now)
        world.effects = []
        world.game_over = False
        world.camera.follow(world.player.centerx, world.player.centery)
        return world

    def merge_save_data(self, data):
        """Overlay a save dict onto this in-progress round (in-game load)."""
        self.player.apply_dict(data["player"])
        self.bombs, self.shards, self.enemies = _load_bombs_shards_enemies(data)
        self.score = data.get("score", self.score)
        self.lives = data.get("lives", self.lives)
        self.last_spawn = data.get("last_spawn", self.last_spawn)
        self.camera.follow(self.player.centerx, self.player.centery)

    def update(self, keys, dt, now):
        if self.game_over:
            return

        self._update_player(keys, dt)
        self._update_camera()
        self._maybe_spawn_enemy(now)
        self._update_bombs(dt)
        self._update_enemies(dt, now)
        self._update_shards(dt, now)
        self._update_effects(dt)

        self.score += 1

    # --- per-frame stages, one responsibility each ------------------------

    def _update_player(self, keys, dt):
        spawn_bomb = self.player.update(keys, dt)
        if spawn_bomb:
            self.bombs.append(self.player.create_bomb())

    def _update_camera(self):
        self.camera.follow(self.player.centerx, self.player.centery)

    def _maybe_spawn_enemy(self, now):
        if len(self.enemies) < MAX_ENEMIES and now - self.last_spawn >= ENEMY_SPAWN_MS:
            side = random.choice(["left", "right"])
            self.enemies.append(
                Enemy(side, self.player.centerx, self.player.centery, camera=self.camera)
            )
            self.last_spawn = now

    def _bomb_should_explode(self, bomb, contact_armed):
        """A bomb detonates once its fuse expires, or the instant any
        enemy touches it — whichever comes first. Contact-triggering is
        gated by contact_armed (whether the bomb existed before this
        tick) so a bomb spawned already overlapping an enemy — e.g.
        dropped at the apex of a jump directly over one — always
        survives its first tick instead of exploding before ever being
        rendered."""
        if bomb.is_ready():
            return True
        if not contact_armed:
            return False
        touching_enemy = next((e for e in self.enemies if bomb.rect.colliderect(e.rect)), None)
        if touching_enemy is not None:
            if self.debug:
                debug_log.log(f"bomb contact-triggered by enemy (type={touching_enemy.type})")
            return True
        return False

    def _explode_bomb(self, bomb):
        self.effects.append(ExplosionEffect(bomb.x, bomb.y, bomb.radius))
        self.player.apply_explosion(bomb.x, bomb.y, bomb.radius)
        for enemy in self.enemies:
            if enemy.killed_by_explosion(bomb.x, bomb.y, bomb.radius):
                if self.debug:
                    debug_log.log(f"bomb killed enemy (type={enemy.type})")
                enemy.take_damage()
        if bomb.has_shrapnel:
            self.shards.extend(
                Shard(bomb.x, bomb.y, angle, SHARD_SPEED * 1.25)
                for angle in [i * math.pi * 2 / 10 for i in range(10)]
            )
        if bomb in self.bombs:
            self.bombs.remove(bomb)
        self.player.bombs_left = min(self.player.bombs_left + 1, BOMB_LIMIT)

    def _update_bombs(self, dt):
        for bomb in self.bombs[:]:
            contact_armed = bomb.armed
            bomb.update(dt)
            if self._bomb_should_explode(bomb, contact_armed):
                self._explode_bomb(bomb)

    def _lose_a_life(self, now):
        """Shared by enemy- and shard-collision handling: deduct a life,
        end the game if that was the last one, otherwise respawn — the
        remaining lives and the score earned so far both survive."""
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self._respawn(now)

    def _update_enemies(self, dt, now):
        for enemy in self.enemies[:]:
            enemy.update(dt)
            if not enemy.dead:
                self._damage_enemy_with_touching_shard(enemy)

            if enemy.dead:
                self._kill_enemy(enemy)
            elif self.player.on_ground and enemy.rect.colliderect(self.player.rect):
                if self.debug:
                    debug_log.log("enemy hit player")
                self._lose_a_life(now)
                if not self.game_over:
                    break

    def _damage_enemy_with_touching_shard(self, enemy):
        for shard in self.shards[:]:
            if shard.rect.colliderect(enemy.rect):
                if self.debug:
                    debug_log.log(f"shard hit enemy (type={enemy.type})")
                enemy.take_damage()
                if shard in self.shards:
                    self.shards.remove(shard)
                return

    def _kill_enemy(self, enemy):
        self.shards.extend(enemy.get_death_shrapnel())
        self.score += 100
        self.enemies.remove(enemy)

    def _update_shards(self, dt, now):
        for shard in self.shards[:]:
            shard.update(dt)
            if shard.rect.colliderect(self.player.rect):
                if self.debug:
                    debug_log.log("shard hit player")
                self._lose_a_life(now)
                break
            if not shard.is_alive():
                self.shards.remove(shard)

    def _update_effects(self, dt):
        for effect in self.effects[:]:
            effect.update(dt)
            if not effect.is_alive():
                self.effects.remove(effect)
