import math
import random

import pygame

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, SHARD_SPEED
from game.utils import clamp
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.hitbox import sync_rect
from game.simulation.shard import Shard


class Enemy:
    def __init__(self, spawn_side, center_x, center_y, camera=None, rng=random):
        self.width = 40
        self.height = 34
        self.type = rng.choices(
            list(ENEMY_TYPES.keys()), [t.spawn_weight for t in ENEMY_TYPES.values()]
        )[0]
        if camera is not None:
            viewport_left, viewport_right = camera.x, camera.x + camera.viewport_width
        else:
            viewport_left = center_x - WIDTH / 2
            viewport_right = center_x + WIDTH / 2
        # If the requested side has no off-screen room (the viewport is
        # already pinned against that world edge), spawn off the opposite
        # edge instead of clamping back onto the visible screen.
        if spawn_side == "left" and viewport_left - self.width - 20 < 0:
            spawn_side = "right"
        elif spawn_side == "right" and viewport_right + 20 + self.width > WORLD_WIDTH:
            spawn_side = "left"
        if spawn_side == "left":
            self.x = viewport_left - self.width - 20
            self.vx = 2.2
        else:
            self.x = viewport_right + 20
            self.vx = -2.2
        self.x = clamp(self.x, WORLD_BORDER, WORLD_WIDTH - WORLD_BORDER - self.width)
        self.y = clamp(
            center_y + rng.uniform(-HEIGHT / 3, HEIGHT / 3),
            WORLD_BORDER,
            WORLD_HEIGHT - WORLD_BORDER - self.height,
        )
        self.color = ENEMY_TYPES[self.type].color
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.dead = False
        self.max_hp = ENEMY_TYPES[self.type].max_hp
        self.hp = self.max_hp
        self._sync_rect()

    def _sync_rect(self):
        self.rect = sync_rect(self.x, self.y, self.width, self.height)

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
        return 0

    def update(self, dt):
        self.x += self.vx
        if self.x <= WORLD_BORDER:
            self.x = WORLD_BORDER
            self.vx *= -1
        elif self.x + self.width >= WORLD_WIDTH - WORLD_BORDER:
            self.x = WORLD_WIDTH - WORLD_BORDER - self.width
            self.vx *= -1
        self._sync_rect()

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
        enemy = cls("left", data["x"], data["y"])
        enemy.x = data["x"]
        enemy.y = data["y"]
        enemy.vx = data["vx"]
        enemy.type = data["type"]
        enemy.color = ENEMY_TYPES[enemy.type].color
        enemy._sync_rect()
        enemy.dead = data["dead"]
        enemy.max_hp = ENEMY_TYPES[enemy.type].max_hp
        enemy.hp = data.get("hp", enemy.max_hp)
        return enemy

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "type": self.type,
            "dead": self.dead,
            "hp": self.hp,
        }

    def get_death_shrapnel(self):
        center_x = self.rect.centerx
        center_y = self.rect.centery
        direction = 0 if self.vx > 0 else math.pi
        pattern = ENEMY_TYPES[self.type].shrapnel_pattern
        return [
            Shard(center_x, center_y, angle, SHARD_SPEED * speed_multiplier, color)
            for angle, speed_multiplier, color in pattern(direction)
        ]
