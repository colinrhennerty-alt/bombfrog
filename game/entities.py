"""Game entity state and physics/logic — no pygame drawing here.

Rendering for these entities lives in game.rendering, kept separate so
this module (and its tests) never need a display surface.
"""

import math
import random

import pygame

from game.config import (
    WIDTH,
    PLAYER_SPEED,
    GRAVITY,
    BOMB_FUSE_MS,
    BOMB_RADIUS,
    BOMB_FORCE,
    BOMB_LIMIT,
    BOMB_COOLDOWN_MS,
    SHARD_SPEED,
    SHARD_LIFETIME,
    HEIGHT,
    DEPTH_SPEED,
    FROG_ANIM_MS,
    FROG_IDLE_FRAME_COUNT,
)
from game.utils import clamp
from game.enemy_types import ENEMY_TYPES
from game.depth import ground_y_for_depth, margin_for_depth, scale_for_depth


class Player:
    def __init__(self):
        self.width = 52
        self.height = 40
        self.depth = 0.55
        self.ground_y = ground_y_for_depth(self.depth)
        self.scale = scale_for_depth(self.depth)
        margin = margin_for_depth(self.depth)
        self.x = clamp(WIDTH // 2 - self.width // 2, margin, WIDTH - margin - self.width)
        self.y = self.ground_y - self.height
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.bombs_left = BOMB_LIMIT
        self.pending_bomb = False
        self.bomb_cooldown = 0
        self.color = (43, 175, 76)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.facing = 1
        self.anim_timer = 0
        self.anim_index = 0
        self.land_timer = 0

    @property
    def centerx(self):
        return self.x + self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2

    def update(self, keys, dt):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
        if self.vx != 0:
            self.facing = 1 if self.vx > 0 else -1

        vdepth = 0
        if keys[pygame.K_UP]:
            vdepth -= DEPTH_SPEED
        if keys[pygame.K_DOWN]:
            vdepth += DEPTH_SPEED
        self.depth = clamp(self.depth + vdepth, 0.0, 1.0)
        self.ground_y = ground_y_for_depth(self.depth)
        self.scale = scale_for_depth(self.depth)

        self.x += self.vx
        margin = margin_for_depth(self.depth)
        self.x = clamp(self.x, margin, WIDTH - margin - self.width)

        old_vy = self.vy
        was_on_ground = self.on_ground
        if not self.on_ground:
            self.vy += GRAVITY
        else:
            self.y = self.ground_y - self.height

        self.y += self.vy
        self.bomb_cooldown = max(0, self.bomb_cooldown - dt)
        spawn_bomb = False
        if self.pending_bomb and old_vy < 0 and self.vy >= 0:
            self.pending_bomb = False
            spawn_bomb = True

        if self.y >= self.ground_y - self.height:
            self.y = self.ground_y - self.height
            self.vy = 0
            self.on_ground = True
            self.pending_bomb = False
            if not was_on_ground:
                self.land_timer = 120

        self.land_timer = max(0, self.land_timer - dt)

        if self.on_ground and (self.vx != 0 or vdepth != 0):
            self.anim_timer += dt
            if self.anim_timer >= FROG_ANIM_MS:
                self.anim_timer = 0
                self.anim_index = (self.anim_index + 1) % FROG_IDLE_FRAME_COUNT
        else:
            self.anim_timer = 0
            self.anim_index = 0

        self.rect.topleft = (self.x, self.y)
        return spawn_bomb

    def jump(self):
        if self.on_ground:
            self.vy = -GRAVITY * 24
            self.on_ground = False
            if self.bombs_left > 0 and self.bomb_cooldown <= 0:
                self.pending_bomb = True
                self.bombs_left -= 1
                self.bomb_cooldown = BOMB_COOLDOWN_MS

    def create_bomb(self):
        bomb_x = self.centerx
        bomb_y = self.ground_y - 16
        return Bomb(bomb_x, bomb_y, self.depth)

    @classmethod
    def from_dict(cls, data):
        player = cls()
        player.apply_dict(data)
        return player

    def apply_dict(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.vx = data["vx"]
        self.vy = data["vy"]
        self.depth = data.get("depth", self.depth)
        self.ground_y = ground_y_for_depth(self.depth)
        self.scale = scale_for_depth(self.depth)
        self.on_ground = data["on_ground"]
        self.bombs_left = data["bombs_left"]
        self.pending_bomb = data["pending_bomb"]
        self.bomb_cooldown = data.get("bomb_cooldown", 0)
        self.rect.topleft = (self.x, self.y)

    def apply_explosion(self, origin_x, origin_y, radius):
        dx = self.centerx - origin_x
        dy = self.centery - origin_y
        dist = math.hypot(dx, dy)
        if dist >= radius:
            return

        strength = (radius - dist) / radius
        push_x = dx / dist if dist else 0
        self.vx += push_x * BOMB_FORCE * strength
        upward = -BOMB_FORCE * 0.7 * strength
        if self.vy > upward:
            self.vy = upward
        self.on_ground = False


class Bomb:
    def __init__(self, x, y, depth=1.0):
        self.x = x
        self.y = y
        self.depth = depth
        self.scale = scale_for_depth(depth)
        self.radius = BOMB_RADIUS
        self.timer = BOMB_FUSE_MS
        self.color = (210, 70, 70)
        self.has_shrapnel = random.random() < 0.05
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    @classmethod
    def from_dict(cls, data):
        bomb = cls(data["x"], data["y"], data.get("depth", 1.0))
        bomb.timer = data["timer"]
        bomb.has_shrapnel = data.get("has_shrapnel", False)
        return bomb

    def update(self, dt):
        self.timer -= dt
        self.rect.center = (self.x, self.y)

    def is_ready(self):
        return self.timer <= 0


class Shard:
    def __init__(self, x, y, angle, speed, color=None):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = SHARD_LIFETIME
        self.radius = 4
        self.color = color or (255, 220, 100)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    @classmethod
    def from_dict(cls, data):
        shard = cls(data["x"], data["y"], 0, 0)
        shard.vx = data["vx"]
        shard.vy = data["vy"]
        shard.life = data["life"]
        shard.color = tuple(data["color"])
        shard.rect.topleft = (shard.x - shard.radius, shard.y - shard.radius)
        return shard

    def update(self, dt):
        self.vy += GRAVITY * 0.2
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        self.rect.topleft = (self.x - self.radius, self.y - self.radius)

    def is_alive(self):
        return self.life > 0 and 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT


class Enemy:
    def __init__(self, spawn_side):
        self.width = 40
        self.height = 34
        self.type = random.choices(
            list(ENEMY_TYPES.keys()), [t.spawn_weight for t in ENEMY_TYPES.values()]
        )[0]
        self.depth = random.uniform(0.1, 0.95)
        if spawn_side == "left":
            self.x = -self.width - 20
            self.vx = 2.2
        else:
            self.x = WIDTH + 20
            self.vx = -2.2
        self.ground_y = ground_y_for_depth(self.depth)
        self.y = self.ground_y - self.height
        self.color = ENEMY_TYPES[self.type].color
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.dead = False
        self.max_hp = ENEMY_TYPES[self.type].max_hp
        self.hp = self.max_hp

    def update(self, dt):
        self.x += self.vx
        margin = margin_for_depth(self.depth)
        if self.x <= margin:
            self.x = margin
            self.vx *= -1
        elif self.x + self.width >= WIDTH - margin:
            self.x = WIDTH - margin - self.width
            self.vx *= -1
        self.rect.topleft = (self.x, self.y)

    def killed_by_explosion(self, origin_x, origin_y, radius):
        dx = self.rect.centerx - origin_x
        dy = self.rect.centery - origin_y
        return math.hypot(dx, dy) < radius * 0.75

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.dead = True

    @classmethod
    def from_dict(cls, data):
        enemy = cls("left")
        enemy.x = data["x"]
        enemy.y = data["y"]
        enemy.vx = data["vx"]
        enemy.type = data["type"]
        enemy.depth = data.get("depth", enemy.depth)
        enemy.ground_y = ground_y_for_depth(enemy.depth)
        enemy.color = ENEMY_TYPES[enemy.type].color
        enemy.rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
        enemy.dead = data["dead"]
        enemy.max_hp = ENEMY_TYPES[enemy.type].max_hp
        enemy.hp = data.get("hp", enemy.max_hp)
        return enemy

    def get_death_shrapnel(self):
        center_x = self.rect.centerx
        center_y = self.rect.centery
        direction = 0 if self.vx > 0 else math.pi
        pattern = ENEMY_TYPES[self.type].shrapnel_pattern
        return [
            Shard(center_x, center_y, angle, SHARD_SPEED * speed_multiplier, color)
            for angle, speed_multiplier, color in pattern(direction)
        ]


class ExplosionEffect:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.life = 260

    def update(self, dt):
        self.life -= dt

    def is_alive(self):
        return self.life > 0
