"""A critter: spawns just off-screen on one side, walks back and forth
across the arena, and bursts into its type's shrapnel when its HP runs out.

The first time the frog comes within ENEMY_NOTICE_RADIUS, the critter rolls
its type's follow_chance once. On a hit it chases the frog until the frog
gets beyond ENEMY_GIVE_UP_RADIUS, then goes back to walking side to side.

A multi-HP critter limps once hurt: its `injury` (0 unhurt, 1 on its last
HP) slows it by up to ENEMY_INJURY_SLOWDOWN, and the renderer reddens it.

Per-type stats (HP, size, spawn weight, shrapnel pattern) come from
game.simulation.enemy_types.ENEMY_TYPES.
"""

import math
import random

from game.config import (
    WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, SHARD_SPEED, ENEMY_ANIM_MS, PLAYER_SIZE,
    ENEMY_SPEED, ENEMY_NOTICE_RADIUS, ENEMY_GIVE_UP_RADIUS, ENEMY_INJURY_SLOWDOWN,
)
from game.utils import clamp
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.hitbox import sync_rect
from game.simulation.obstacles import blocks, feet_rect
from game.simulation.rect import Rect
from game.simulation.shard import Shard


def size_for_type(enemy_type):
    """Hitbox (width, height): the frog's height times the type's
    height_vs_frog, with width following the critter art's proportions."""
    spec = ENEMY_TYPES[enemy_type]
    height = round(PLAYER_SIZE[1] * spec.height_vs_frog)
    return round(height * spec.art_aspect), height


class Enemy:
    def __init__(self, spawn_side, center_x, center_y, camera=None, rng=random):
        self.type = rng.choices(
            list(ENEMY_TYPES.keys()), [t.spawn_weight for t in ENEMY_TYPES.values()]
        )[0]
        self.width, self.height = size_for_type(self.type)
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
            self.vx = ENEMY_SPEED
        else:
            self.x = viewport_right + 20
            self.vx = -ENEMY_SPEED
        self.x = clamp(self.x, WORLD_BORDER, WORLD_WIDTH - WORLD_BORDER - self.width)
        self.y = clamp(
            center_y + rng.uniform(-HEIGHT / 3, HEIGHT / 3),
            WORLD_BORDER,
            WORLD_HEIGHT - WORLD_BORDER - self.height,
        )
        self.color = ENEMY_TYPES[self.type].color
        self.rect = Rect(0, 0, self.width, self.height)
        self.dead = False
        self.max_hp = ENEMY_TYPES[self.type].max_hp
        self.hp = self.max_hp
        self.anim_timer = 0
        self.anim_index = 0
        self.vy = 0.0
        self.follow_rolled = False
        self.following = False
        self.rng = rng
        self._sync_rect()

    def _sync_rect(self):
        self.rect = sync_rect(self.x, self.y, self.width, self.height)

    @property
    def injury(self):
        """0.0 unhurt, 1.0 one hit from death; one-HP types are never hurt."""
        if self.max_hp <= 1:
            return 0.0
        return clamp((self.max_hp - self.hp) / (self.max_hp - 1), 0.0, 1.0)

    @property
    def speed(self):
        return ENEMY_SPEED * (1 - ENEMY_INJURY_SLOWDOWN * self.injury)

    @property
    def shadow_anchor(self):
        """Where rendering should anchor this entity's shadow: an
        upright rect entity reads as cast on the ground beneath its feet
        (rect.midbottom), not floating near its torso/center (see
        game.rendering.entities.draw_scene)."""
        return self.rect.midbottom

    @property
    def shadow_radius(self):
        return self.width

    @property
    def shadow_height_offset(self):
        return 0

    def _step_blocked(self, obstacles, new_x, new_y):
        return blocks(
            obstacles,
            feet_rect(self.x, self.y, self.width, self.height),
            feet_rect(new_x, new_y, self.width, self.height),
        )

    def update(self, dt, target=None, obstacles=()):
        """`target` is the frog's (centerx, centery); without one the
        critter just walks side to side. `obstacles` block its feet: a
        wandering critter turns around at one like at the arena wall, a
        chasing one keeps its other axis and slides around it."""
        if target is not None:
            self._steer_toward(target)
        if self._step_blocked(obstacles, self.x + self.vx, self.y):
            if not self.following:
                self.vx *= -1
        else:
            self.x += self.vx
        new_y = clamp(self.y + self.vy, WORLD_BORDER, WORLD_HEIGHT - WORLD_BORDER - self.height)
        if not self._step_blocked(obstacles, self.x, new_y):
            self.y = new_y
        if self.x <= WORLD_BORDER:
            self.x = WORLD_BORDER
            self.vx *= -1
        elif self.x + self.width >= WORLD_WIDTH - WORLD_BORDER:
            self.x = WORLD_WIDTH - WORLD_BORDER - self.width
            self.vx *= -1
        self._update_animation(dt)
        self._sync_rect()

    def _steer_toward(self, target):
        dx = target[0] - self.rect.centerx
        dy = target[1] - self.rect.centery
        distance = math.hypot(dx, dy)
        if not self.follow_rolled and distance <= ENEMY_NOTICE_RADIUS:
            self.follow_rolled = True
            self.following = self.rng.random() < ENEMY_TYPES[self.type].follow_chance
        if self.following and distance > ENEMY_GIVE_UP_RADIUS:
            self.following = False
            self.vy = 0.0
            heading = self.vx if self.vx != 0 else dx
            self.vx = math.copysign(self.speed, heading)
        if self.following and distance > 0:
            self.vx = self.speed * dx / distance
            self.vy = self.speed * dy / distance

    def _update_animation(self, dt):
        # anim_index counts up without wrapping; the renderer wraps it by
        # each critter's own frame count, which the sim doesn't know.
        self.anim_timer += dt
        if self.anim_timer >= ENEMY_ANIM_MS:
            self.anim_timer = 0
            self.anim_index += 1

    def killed_by_explosion(self, origin_x, origin_y, radius):
        dx = self.rect.centerx - origin_x
        dy = self.rect.centery - origin_y
        return math.hypot(dx, dy) < radius * 0.75

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.dead = True
        elif not self.following:
            # Followers pick up their slower speed on their next steer.
            self.vx = math.copysign(self.speed, self.vx)

    @classmethod
    def from_dict(cls, data):
        """Builds an Enemy purely from saved data — bypasses __init__
        (which rolls a random type/spawn-side/y-offset) since every field
        is already fully determined by `data`."""
        enemy = cls.__new__(cls)
        enemy.x = data["x"]
        enemy.y = data["y"]
        enemy.vx = data["vx"]
        enemy.type = data["type"]
        enemy.width, enemy.height = size_for_type(enemy.type)
        enemy.color = ENEMY_TYPES[enemy.type].color
        enemy.rect = Rect(0, 0, enemy.width, enemy.height)
        enemy._sync_rect()
        enemy.dead = data["dead"]
        enemy.max_hp = ENEMY_TYPES[enemy.type].max_hp
        enemy.hp = data.get("hp", enemy.max_hp)
        enemy.anim_timer = 0
        enemy.anim_index = 0
        enemy.vy = data.get("vy", 0.0)
        enemy.follow_rolled = data.get("follow_rolled", False)
        enemy.following = data.get("following", False)
        enemy.rng = random
        return enemy

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "type": self.type,
            "dead": self.dead,
            "hp": self.hp,
            "vy": self.vy,
            "follow_rolled": self.follow_rolled,
            "following": self.following,
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
