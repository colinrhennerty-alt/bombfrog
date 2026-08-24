import math

import pygame

from game.config import WIDTH, HEIGHT, GRAVITY, SHARD_LIFETIME


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
