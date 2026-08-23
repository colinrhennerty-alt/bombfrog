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

from game.config import MAX_ENEMIES, ENEMY_SPAWN_MS, SHARD_SPEED, BOMB_LIMIT
from game.entities import Player, Bomb, Shard, Enemy, ExplosionEffect


def _apply_player_dict(player, data):
    player.x = data["x"]
    player.y = data["y"]
    player.vx = data["vx"]
    player.vy = data["vy"]
    player.on_ground = data["on_ground"]
    player.bombs_left = data["bombs_left"]
    player.pending_bomb = data["pending_bomb"]
    player.bomb_cooldown = data.get("bomb_cooldown", 0)
    player.rect.topleft = (player.x, player.y)


class World:
    def __init__(self, now=0):
        self.reset(now)

    def reset(self, now=0):
        self.player = Player()
        self.bombs = []
        self.shards = []
        self.enemies = []
        self.effects = []
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.last_spawn = now

    @classmethod
    def from_save_data(cls, data, now=0):
        """Build a fresh World from a save dict (the menu's "Load Game")."""
        world = cls.__new__(cls)
        world.player = Player()
        _apply_player_dict(world.player, data["player"])
        world.bombs = [Bomb.from_dict(b) for b in data["bombs"]]
        world.shards = [Shard.from_dict(s) for s in data["shards"]]
        world.enemies = [Enemy.from_dict(e) for e in data["enemies"]]
        world.score = data.get("score", 0)
        world.lives = data.get("lives", 3)
        world.last_spawn = data.get("last_spawn", now)
        world.effects = []
        world.game_over = False
        return world

    def merge_save_data(self, data):
        """Overlay a save dict onto this in-progress round (in-game load)."""
        _apply_player_dict(self.player, data["player"])
        self.bombs = [Bomb.from_dict(b) for b in data["bombs"]]
        self.shards = [Shard.from_dict(s) for s in data["shards"]]
        self.enemies = [Enemy.from_dict(e) for e in data["enemies"]]
        self.score = data.get("score", self.score)
        self.lives = data.get("lives", self.lives)
        self.last_spawn = data.get("last_spawn", self.last_spawn)

    def update(self, keys, dt, now):
        if self.game_over:
            return

        spawn_bomb = self.player.update(keys, dt)

        if spawn_bomb:
            self.bombs.append(self.player.create_bomb())

        if len(self.enemies) < MAX_ENEMIES and now - self.last_spawn >= ENEMY_SPAWN_MS:
            side = random.choice(["left", "right"])
            self.enemies.append(Enemy(side))
            self.last_spawn = now

        for bomb in self.bombs[:]:
            bomb.update(dt)
            # explode if fuse ready OR if any enemy touches the bomb
            triggered = False
            if bomb.is_ready():
                triggered = True
            else:
                for e in self.enemies:
                    if bomb.rect.colliderect(e.rect):
                        triggered = True
                        break

            if triggered:
                self.effects.append(ExplosionEffect(bomb.x, bomb.y, bomb.radius))
                self.player.apply_explosion(bomb.x, bomb.y, bomb.radius)
                for enemy in self.enemies:
                    if enemy.killed_by_explosion(bomb.x, bomb.y, bomb.radius):
                        enemy.take_damage()
                if bomb.has_shrapnel:
                    self.shards.extend(
                        Shard(bomb.x, bomb.y, angle, SHARD_SPEED * 1.25)
                        for angle in [i * math.pi * 2 / 10 for i in range(10)]
                    )
                if bomb in self.bombs:
                    self.bombs.remove(bomb)
                self.player.bombs_left = min(self.player.bombs_left + 1, BOMB_LIMIT)

        for enemy in self.enemies[:]:
            enemy.update(dt)
            if not enemy.dead:
                for shard in self.shards[:]:
                    if shard.rect.colliderect(enemy.rect):
                        enemy.take_damage()
                        if shard in self.shards:
                            self.shards.remove(shard)
                        break

            if enemy.dead:
                self.shards.extend(enemy.get_death_shrapnel())
                self.score += 100
                self.enemies.remove(enemy)
            elif enemy.rect.colliderect(self.player.rect):
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                else:
                    self.reset(now)
                    break

        for shard in self.shards[:]:
            shard.update(dt)
            if shard.rect.colliderect(self.player.rect):
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                    break
                else:
                    self.reset(now)
                    break
            if not shard.is_alive():
                self.shards.remove(shard)

        for effect in self.effects[:]:
            effect.update(dt)
            if not effect.is_alive():
                self.effects.remove(effect)

        self.score += 1
