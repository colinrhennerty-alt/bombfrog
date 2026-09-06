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

    # Fraction of the viewport, centered, that the target can move within
    # before the camera reacts — the classic "camera deadzone"/"scroll box"
    # used in platformers so the camera doesn't recenter on every twitch
    # of player movement.
    DEADZONE_WIDTH_RATIO = 0.4
    DEADZONE_HEIGHT_RATIO = 0.4

    def snap_to(self, target_x, target_y):
        """Hard recenter on the target, no deadzone — for one-time events
        (respawn, loading a save, a fresh round) where the camera should
        jump immediately rather than ease in from wherever it was."""
        self.x = clamp(target_x - self.viewport_width / 2, 0, self.world_width - self.viewport_width)
        self.y = clamp(target_y - self.viewport_height / 2, 0, self.world_height - self.viewport_height)

    def follow(self, target_x, target_y):
        """Per-frame camera tracking with a deadzone: the camera only
        moves once the target exits a centered box on screen, and then
        only by enough to pin the target back at that box's edge (not
        all the way to screen center) — unlike snap_to, which always
        hard-recenters."""
        screen_x, screen_y = target_x - self.x, target_y - self.y

        half_w = (self.viewport_width * self.DEADZONE_WIDTH_RATIO) / 2
        half_h = (self.viewport_height * self.DEADZONE_HEIGHT_RATIO) / 2
        center_x, center_y = self.viewport_width / 2, self.viewport_height / 2

        if screen_x < center_x - half_w:
            self.x -= (center_x - half_w) - screen_x
        elif screen_x > center_x + half_w:
            self.x += screen_x - (center_x + half_w)

        if screen_y < center_y - half_h:
            self.y -= (center_y - half_h) - screen_y
        elif screen_y > center_y + half_h:
            self.y += screen_y - (center_y + half_h)

        self.x = clamp(self.x, 0, self.world_width - self.viewport_width)
        self.y = clamp(self.y, 0, self.world_height - self.viewport_height)

    def apply(self, world_x, world_y):
        return world_x - self.x, world_y - self.y

    def apply_rect(self, rect):
        screen_rect = rect.copy()
        screen_rect.x -= int(self.x)
        screen_rect.y -= int(self.y)
        return screen_rect
