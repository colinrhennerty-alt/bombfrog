"""Player entity state and physics/logic — no pygame drawing here.

Rendering lives in game.rendering, kept separate so this module (and
its tests) never need a display surface.
"""

import math

import pygame

from game.config import (
    WORLD_WIDTH,
    WORLD_HEIGHT,
    WORLD_BORDER,
    PLAYER_SPEED,
    GRAVITY,
    BOMB_FORCE,
    FROG_ANIM_MS,
    FROG_IDLE_FRAME_COUNT,
)
from game.utils import clamp
from game.simulation.hitbox import sync_rect
from game.simulation.bomb import Bomb
from game.simulation.bomb_launcher import BombLauncher


class Player:
    def __init__(self):
        self.width = 52
        self.height = 40
        self.x = clamp(WORLD_WIDTH // 2 - self.width // 2, WORLD_BORDER, WORLD_WIDTH - WORLD_BORDER - self.width)
        self.y = clamp(WORLD_HEIGHT // 2 - self.height // 2, WORLD_BORDER, WORLD_HEIGHT - WORLD_BORDER - self.height)
        self.vx = 0
        self.vy = 0
        self.jump_offset = 0
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
    def shadow_anchor(self):
        """Where rendering should anchor this entity's shadow: an
        upright rect entity reads as cast on the ground beneath its feet
        (rect.midbottom), not floating near its torso/center (see
        rendering.draw_scene)."""
        return self.rect.midbottom

    @property
    def shadow_radius(self):
        return self.width

    @property
    def shadow_height_offset(self):
        return self.jump_offset

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
        self.rect = sync_rect(self.x, self.y, self.width, self.height)

    def update(self, keys, dt):
        self._apply_horizontal_movement(keys)
        vy_input = self._apply_vertical_movement(keys)
        self.bomb_launcher.tick_cooldown(dt)
        spawn_bomb = self._apply_jump_physics(dt)
        self._update_animation(dt, vy_input)
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
        self.x = clamp(self.x, WORLD_BORDER, WORLD_WIDTH - WORLD_BORDER - self.width)

    def _apply_vertical_movement(self, keys):
        vy_input = 0
        if keys[pygame.K_UP]:
            vy_input = -PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            vy_input = PLAYER_SPEED
        self.y += vy_input
        self.y = clamp(self.y, WORLD_BORDER, WORLD_HEIGHT - WORLD_BORDER - self.height)
        return vy_input

    def _apply_jump_physics(self, dt):
        old_vy = self.vy
        was_on_ground = self.on_ground
        self._integrate_gravity()
        spawn_bomb = self.bomb_launcher.check_apex(old_vy, self.vy)
        self._handle_landing(was_on_ground)
        self.land_timer = max(0, self.land_timer - dt)
        return spawn_bomb

    def _integrate_gravity(self):
        if not self.on_ground:
            self.vy += GRAVITY
            self.jump_offset += self.vy

    def _handle_landing(self, was_on_ground):
        if self.jump_offset < 0:
            return
        self.jump_offset = 0
        self.vy = 0
        self.on_ground = True
        self.bomb_launcher.cancel_pending()
        if not was_on_ground:
            self.land_timer = 120

    def _update_animation(self, dt, vy_input):
        if self.on_ground and (self.vx != 0 or vy_input != 0):
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
        bomb_y = self.y + self.height
        return Bomb(bomb_x, bomb_y, fall_offset=self.jump_offset)

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
        self.on_ground = data["on_ground"]
        self.bomb_launcher.apply_dict(data)
        self._sync_rect()

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "on_ground": self.on_ground,
            **self.bomb_launcher.to_dict(),
        }

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
