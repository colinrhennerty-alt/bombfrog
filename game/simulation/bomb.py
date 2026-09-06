import random

import pygame

from game.config import BOMB_RADIUS, BOMB_FUSE_MS, BOMB_FALL_SPEED, BOMB_CONTACT_GRACE_MS


class Bomb:
    def __init__(self, x, y, fall_offset=0, rng=random):
        self.x = x
        self.y = y
        self.radius = BOMB_RADIUS
        self.timer = BOMB_FUSE_MS
        self.color = (210, 70, 70)
        self.has_shrapnel = rng.random() < 0.05
        self.fall_offset = fall_offset
        self.age_ms = 0
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    @property
    def shadow_anchor(self):
        """Where rendering should anchor this entity's shadow: circular
        entities have no "feet", so their rect.center is the natural
        anchor (see rendering.draw_scene)."""
        return self.rect.center

    @property
    def armed(self):
        """Whether the bomb can contact-explode yet. False for a short
        grace period after spawning — even though a single simulation
        tick technically satisfies "the bomb existed before this frame,"
        16ms is imperceptible; a bomb dropped directly on an enemy would
        detonate before a player could actually see it appear."""
        return self.age_ms >= BOMB_CONTACT_GRACE_MS

    @classmethod
    def from_dict(cls, data):
        bomb = cls(data["x"], data["y"], data.get("fall_offset", 0))
        bomb.timer = data["timer"]
        bomb.has_shrapnel = data.get("has_shrapnel", False)
        bomb.age_ms = BOMB_CONTACT_GRACE_MS  # already existed in the world before saving
        return bomb

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "timer": self.timer,
            "has_shrapnel": self.has_shrapnel,
            "fall_offset": self.fall_offset,
        }

    def update(self, dt):
        self.timer -= dt
        self.rect.center = (self.x, self.y)
        self._ease_fall_offset(dt)
        self.age_ms += dt

    def _ease_fall_offset(self, dt):
        if self.fall_offset == 0:
            return
        step = BOMB_FALL_SPEED * (dt / 16)
        if self.fall_offset < 0:
            self.fall_offset = min(0, self.fall_offset + step)
        else:
            self.fall_offset = max(0, self.fall_offset - step)

    def is_ready(self):
        return self.timer <= 0 and self.fall_offset == 0
