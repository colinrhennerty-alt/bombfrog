"""The menu <-> playing <-> game-over state machine.

This is the logic that used to live as loose local variables and a
sprawling if/elif KEYDOWN dispatch inside main.py's run_game(). GameApp
owns that state; main.py stays responsible only for the pygame event
pump and handing frames to game.rendering.
"""

from game.config import SAVE_FILE, LEVEL_FILE
from game.persistence.save_load import load_game
from game.simulation.world import World
from game.scene.editor_state import EditorState, PAN_STEP


class GameApp:
    def __init__(self, now=0, save_file=SAVE_FILE, level_file=LEVEL_FILE, debug=False):
        self.save_file = save_file
        self.level_file = level_file
        self.menu_options = ["Start Game", "Load Game", "Map Editor", "Quit"]
        self.selected = 0
        self.world = None
        self.editor_state = None
        self.high_score = 0
        self.running = True
        self.state = "menu"
        self.debug = debug

    def handle_action(self, action, now):
        if self.state == "menu":
            self._handle_menu_action(action, now)
        elif self.state == "editor":
            self._handle_editor_action(action, now)
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
            loaded = self._load_high_score(default=0)
            if loaded:
                self.world = World.from_save_data(loaded, now)
                self.state = "playing"
        elif choice == "Map Editor":
            self.editor_state = EditorState()
            self.state = "editor"
        elif choice == "Quit":
            self.running = False

    def _load_high_score(self, default):
        """Load the save file, if any, updating high_score from it.
        Returns the loaded dict (falsy if there was nothing to load)."""
        loaded = load_game(self.save_file)
        if loaded:
            self.high_score = loaded.get("high_score", default)
        return loaded

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
            self.world.save(self.save_file, self.high_score)
        elif action == "load":
            loaded = self._load_high_score(default=self.high_score)
            if loaded:
                self.world.merge_save_data(loaded)
        elif action == "menu_back":
            self.state = "menu"
        elif action == "toggle_debug":
            self.debug = not self.debug

    def _handle_editor_action(self, action, now):
        editor = self.editor_state
        if action == "pan_up":
            editor.pan(0, -PAN_STEP)
        elif action == "pan_down":
            editor.pan(0, PAN_STEP)
        elif action == "pan_left":
            editor.pan(-PAN_STEP, 0)
        elif action == "pan_right":
            editor.pan(PAN_STEP, 0)
        elif action.startswith("select_tile_"):
            editor.select_tile(int(action.removeprefix("select_tile_")))
        elif action == "menu_back":
            self.state = "menu"

    def tick(self, keys, dt, now):
        if self.state != "playing":
            return
        self.world.debug = self.debug
        self.world.update(keys, dt, now)
        if self.world.game_over:
            self.high_score = max(self.high_score, self.world.score)
