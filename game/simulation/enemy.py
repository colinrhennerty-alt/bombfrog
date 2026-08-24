import math
import random

import pygame

from game.config import WIDTH, SHARD_SPEED
from game.simulation.depth import ground_y_for_depth, margin_for_depth
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.hitbox import sync_rect_for_depth
from game.simulation.shard import Shard


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
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.dead = False
        self.max_hp = ENEMY_TYPES[self.type].max_hp
        self.hp = self.max_hp
        self._sync_rect()

    def _sync_rect(self):
        self.rect = sync_rect_for_depth(self.x, self.y, self.width, self.height, self.depth)

    def update(self, dt):
        self.x += self.vx
        margin = margin_for_depth(self.depth)
        if self.x <= margin:
            self.x = margin
            self.vx *= -1
        elif self.x + self.width >= WIDTH - margin:
            self.x = WIDTH - margin - self.width
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
        enemy = cls("left")
        enemy.x = data["x"]
        enemy.y = data["y"]
        enemy.vx = data["vx"]
        enemy.type = data["type"]
        enemy.depth = data.get("depth", enemy.depth)
        enemy.ground_y = ground_y_for_depth(enemy.depth)
        enemy.color = ENEMY_TYPES[enemy.type].color
        enemy._sync_rect()
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
