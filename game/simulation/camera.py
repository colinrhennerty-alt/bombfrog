"""Pure math for the camera: tracks a target in world space and produces
a world -> screen translation, clamped so the viewport never shows past
the world's edges. No pygame dependency — used by both simulation
(game.simulation.world, to own/update it) and rendering (to translate
entity positions before drawing).
"""

from game.utils import clamp


class Camera:
    def __init__(self, viewport_width, viewport_height, world_width, world_height):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.world_width = world_width
        self.world_height = world_height
        self.x = 0
        self.y = 0

    def follow(self, target_x, target_y):
        self.x = clamp(target_x - self.viewport_width / 2, 0, self.world_width - self.viewport_width)
        self.y = clamp(target_y - self.viewport_height / 2, 0, self.world_height - self.viewport_height)

    def apply(self, world_x, world_y):
        return world_x - self.x, world_y - self.y

    def apply_rect(self, rect):
        screen_rect = rect.copy()
        screen_rect.x -= int(self.x)
        screen_rect.y -= int(self.y)
        return screen_rect
