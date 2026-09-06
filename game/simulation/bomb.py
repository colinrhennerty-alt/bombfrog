import random

import pygame

from game.config import BOMB_RADIUS, BOMB_FUSE_MS, BOMB_FALL_SPEED


class Bomb:
    def __init__(self, x, y, fall_offset=0):
        self.x = x
        self.y = y
        self.radius = BOMB_RADIUS
        self.timer = BOMB_FUSE_MS
        self.color = (210, 70, 70)
        self.has_shrapnel = random.random() < 0.05
        self.fall_offset = fall_offset
        self.armed = False
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    @classmethod
    def from_dict(cls, data):
        bomb = cls(data["x"], data["y"], data.get("fall_offset", 0))
        bomb.timer = data["timer"]
        bomb.has_shrapnel = data.get("has_shrapnel", False)
        bomb.armed = True  # already existed in the world before saving
        return bomb

    def update(self, dt):
        self.timer -= dt
        self.rect.center = (self.x, self.y)
        self._ease_fall_offset(dt)
        self.armed = True

    def _ease_fall_offset(self, dt):
        if self.fall_offset == 0:
            return
        step = BOMB_FALL_SPEED * (dt / 16)
        if self.fall_offset < 0:
            self.fall_offset = min(0, self.fall_offset + step)
        else:
            self.fall_offset = max(0, self.fall_offset - step)

    def is_ready(self):
        return self.timer <= 0
