"""Player entity state and physics/logic — no pygame drawing here.

Rendering lives in game.rendering, kept separate so this module (and
its tests) never need a display surface.
"""

import math

import pygame

from game.config import (
    WIDTH,
    PLAYER_SPEED,
    GRAVITY,
    BOMB_FORCE,
    BOMB_LIMIT,
    BOMB_COOLDOWN_MS,
    DEPTH_SPEED,
    FROG_ANIM_MS,
    FROG_IDLE_FRAME_COUNT,
)
from game.utils import clamp
from game.simulation.depth import ground_y_for_depth, margin_for_depth, scale_for_depth
from game.simulation.bomb import Bomb


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
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.facing = 1
        self.anim_timer = 0
        self.anim_index = 0
        self.land_timer = 0
        self._sync_rect()

    @property
    def centerx(self):
        return self.x + self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2

    def _sync_rect(self):
        """Collision box tracks the depth-scaled visual size, anchored at
        the same bottom-center point rendering draws the sprite at — so
        the hitbox always matches what's on screen, at any depth."""
        w = max(1, int(self.width * self.scale))
        h = max(1, int(self.height * self.scale))
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.midbottom = (self.centerx, self.y + self.height)

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

        self._sync_rect()
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
        self._sync_rect()

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
