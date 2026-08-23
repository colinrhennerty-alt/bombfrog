"""The menu <-> playing <-> game-over state machine.

This is the logic that used to live as loose local variables and a
sprawling if/elif KEYDOWN dispatch inside main.py's run_game(). GameApp
owns that state; main.py stays responsible only for the pygame event
pump and handing frames to game.rendering.
"""

from game.config import SAVE_FILE
from game.persistence import save_game, load_game
from game.world import World


class GameApp:
    def __init__(self, now=0, save_file=SAVE_FILE):
        self.save_file = save_file
        self.menu_options = ["Start Game", "Load Game", "Quit"]
        self.selected = 0
        self.world = None
        self.high_score = 0
        self.running = True
        self.state = "menu"

    def handle_action(self, action, now):
        if self.state == "menu":
            self._handle_menu_action(action, now)
        else:
            self._handle_playing_action(action, now)

    def _handle_menu_action(self, action, now):
        if action == "menu_up":
            self.selected = (self.selected - 1) % len(self.menu_options)
        elif action == "menu_down":
            self.selected = (self.selected + 1) % len(self.menu_options)
        elif action == "menu_confirm":
            self._confirm_menu_choice(now)

    def _confirm_menu_choice(self, now):
        choice = self.menu_options[self.selected]
        if choice == "Start Game":
            self.world = World(now)
            self.state = "playing"
        elif choice == "Load Game":
            loaded = load_game(self.save_file)
            if loaded:
                self.world = World.from_save_data(loaded, now)
                self.high_score = loaded.get("high_score", 0)
                self.state = "playing"
        elif choice == "Quit":
            self.running = False

    def _handle_playing_action(self, action, now):
        if action == "space":
            if not self.world.game_over:
                self.world.player.jump()
            else:
                self.world.reset(now)
        elif action == "restart":
            if self.world.game_over:
                self.world.reset(now)
        elif action == "save":
            save_game(
                self.save_file, self.world.player, self.world.bombs, self.world.shards,
                self.world.enemies, self.world.score, self.high_score, self.world.lives,
                self.world.last_spawn,
            )
        elif action == "load":
            loaded = load_game(self.save_file)
            if loaded:
                self.world.merge_save_data(loaded)
                self.high_score = loaded.get("high_score", self.high_score)
        elif action == "menu_back":
            self.state = "menu"

    def tick(self, keys, dt, now):
        if self.state != "playing":
            return
        self.world.update(keys, dt, now)
        if self.world.game_over:
            self.high_score = max(self.high_score, self.world.score)
