import math

from game.config import WORLD_WIDTH, WORLD_HEIGHT, GRAVITY, SHARD_LIFETIME
from game.simulation.rect import Rect


class Shard:
    def __init__(self, x, y, angle, speed, color=None):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = SHARD_LIFETIME
        self.radius = 4
        self.color = color or (255, 220, 100)
        self.rect = Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    @classmethod
    def from_dict(cls, data):
        shard = cls(data["x"], data["y"], 0, 0)
        shard.vx = data["vx"]
        shard.vy = data["vy"]
        shard.life = data["life"]
        shard.color = tuple(data["color"])
        shard.rect = shard.rect.moved_topleft(shard.x - shard.radius, shard.y - shard.radius)
        return shard

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "life": self.life,
            "color": list(self.color),
        }

    def update(self, dt):
        self.vy += GRAVITY * 0.2
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        self.rect = self.rect.moved_topleft(self.x - self.radius, self.y - self.radius)

    def is_alive(self):
        return self.life > 0 and 0 <= self.x <= WORLD_WIDTH and 0 <= self.y <= WORLD_HEIGHT

    @property
    def shadow_anchor(self):
        """Where rendering should anchor this entity's shadow: circular
        entities have no "feet", so their rect.center is the natural
        anchor (see rendering.draw_scene)."""
        return self.rect.center

    @property
    def shadow_radius(self):
        return self.radius

    @property
    def shadow_height_offset(self):
        return 0
