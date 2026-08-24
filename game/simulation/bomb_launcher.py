"""A player's bomb inventory and throw-timing.

Split out of Player: bomb count, cooldown, and jump-apex spawn timing
are projectile-lifecycle bookkeeping, not player physics.
"""

from game.config import BOMB_LIMIT, BOMB_COOLDOWN_MS


class BombLauncher:
    def __init__(self):
        self.bombs_left = BOMB_LIMIT
        self.pending_bomb = False
        self.cooldown = 0

    def tick_cooldown(self, dt):
        self.cooldown = max(0, self.cooldown - dt)

    def try_launch(self):
        """Called when the player jumps. Consumes a bomb and arms the
        apex-triggered spawn, if one is available."""
        if self.bombs_left > 0 and self.cooldown <= 0:
            self.pending_bomb = True
            self.bombs_left -= 1
            self.cooldown = BOMB_COOLDOWN_MS

    def check_apex(self, old_vy, new_vy):
        """True exactly once, the tick vy crosses from rising to falling
        while a bomb is pending."""
        if self.pending_bomb and old_vy < 0 and new_vy >= 0:
            self.pending_bomb = False
            return True
        return False

    def cancel_pending(self):
        self.pending_bomb = False

    def refill_one(self):
        self.bombs_left = min(self.bombs_left + 1, BOMB_LIMIT)

    def apply_dict(self, data):
        self.bombs_left = data["bombs_left"]
        self.pending_bomb = data["pending_bomb"]
        self.cooldown = data.get("bomb_cooldown", 0)
