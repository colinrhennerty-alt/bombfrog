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
    DEPTH_SPEED,
    FROG_ANIM_MS,
    FROG_IDLE_FRAME_COUNT,
)
from game.utils import clamp
from game.simulation.depth import ground_y_for_depth, margin_for_depth, scale_for_depth
from game.simulation.bomb import Bomb
from game.simulation.bomb_launcher import BombLauncher


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
        self.bomb_launcher = BombLauncher()
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

    @property
    def bombs_left(self):
        return self.bomb_launcher.bombs_left

    @bombs_left.setter
    def bombs_left(self, value):
        self.bomb_launcher.bombs_left = value

    @property
    def pending_bomb(self):
        return self.bomb_launcher.pending_bomb

    @pending_bomb.setter
    def pending_bomb(self, value):
        self.bomb_launcher.pending_bomb = value

    @property
    def bomb_cooldown(self):
        return self.bomb_launcher.cooldown

    @bomb_cooldown.setter
    def bomb_cooldown(self, value):
        self.bomb_launcher.cooldown = value

    def _sync_rect(self):
        """Collision box tracks the depth-scaled visual size, anchored at
        the same bottom-center point rendering draws the sprite at — so
        the hitbox always matches what's on screen, at any depth."""
        w = max(1, int(self.width * self.scale))
        h = max(1, int(self.height * self.scale))
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.midbottom = (self.centerx, self.y + self.height)

    def update(self, keys, dt):
        self._apply_horizontal_movement(keys)
        vdepth = self._apply_depth_movement(keys)
        self.bomb_launcher.tick_cooldown(dt)
        spawn_bomb = self._apply_vertical_physics(dt)
        self._update_animation(dt, vdepth)
        self._sync_rect()
        return spawn_bomb

    def _apply_horizontal_movement(self, keys):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
        if self.vx != 0:
            self.facing = 1 if self.vx > 0 else -1

        self.x += self.vx
        margin = margin_for_depth(self.depth)
        self.x = clamp(self.x, margin, WIDTH - margin - self.width)

    def _apply_depth_movement(self, keys):
        vdepth = 0
        if keys[pygame.K_UP]:
            vdepth -= DEPTH_SPEED
        if keys[pygame.K_DOWN]:
            vdepth += DEPTH_SPEED
        self.depth = clamp(self.depth + vdepth, 0.0, 1.0)
        self.ground_y = ground_y_for_depth(self.depth)
        self.scale = scale_for_depth(self.depth)
        return vdepth

    def _apply_vertical_physics(self, dt):
        old_vy = self.vy
        was_on_ground = self.on_ground
        if not self.on_ground:
            self.vy += GRAVITY
        else:
            self.y = self.ground_y - self.height

        self.y += self.vy
        spawn_bomb = self.bomb_launcher.check_apex(old_vy, self.vy)

        if self.y >= self.ground_y - self.height:
            self.y = self.ground_y - self.height
            self.vy = 0
            self.on_ground = True
            self.bomb_launcher.cancel_pending()
            if not was_on_ground:
                self.land_timer = 120

        self.land_timer = max(0, self.land_timer - dt)
        return spawn_bomb

    def _update_animation(self, dt, vdepth):
        if self.on_ground and (self.vx != 0 or vdepth != 0):
            self.anim_timer += dt
            if self.anim_timer >= FROG_ANIM_MS:
                self.anim_timer = 0
                self.anim_index = (self.anim_index + 1) % FROG_IDLE_FRAME_COUNT
        else:
            self.anim_timer = 0
            self.anim_index = 0

    def jump(self):
        if self.on_ground:
            self.vy = -GRAVITY * 24
            self.on_ground = False
            self.bomb_launcher.try_launch()

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
        self.bomb_launcher.apply_dict(data)
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
