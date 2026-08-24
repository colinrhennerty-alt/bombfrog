import random

import pygame

from game.config import BOMB_RADIUS, BOMB_FUSE_MS
from game.simulation.depth import scale_for_depth


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
