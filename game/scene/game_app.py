"""The top-level mode state machine: menu <-> playing <-> editor.

GameApp holds the current mode, the active World or EditorState, and the
session's high score, and turns abstract actions (from game.input) into
mode changes and game commands. main.py only pumps pygame events into
`handle_action` / `tick` and draws whatever mode is active.
"""

from game.config import SAVE_FILE, LEVEL_FILE
from game.persistence.save_load import load_game
from game.simulation.world import World
from game.scene.editor_state import EditorState, PAN_STEP
from game.scene.modes import Mode
from game.input.actions import Action, SELECT_TILE_ACTIONS


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
        self.state = Mode.MENU
        self.debug = debug

    def handle_action(self, action, now):
        if self.state == Mode.MENU:
            self._handle_menu_action(action, now)
        elif self.state == Mode.EDITOR:
            self._handle_editor_action(action, now)
        else:
            self._handle_playing_action(action, now)

    def _handle_menu_action(self, action, now):
        if action == Action.MENU_UP:
            self.selected = (self.selected - 1) % len(self.menu_options)
        elif action == Action.MENU_DOWN:
            self.selected = (self.selected + 1) % len(self.menu_options)
        elif action == Action.MENU_CONFIRM:
            self._confirm_menu_choice(now)

    def _confirm_menu_choice(self, now):
        choice = self.menu_options[self.selected]
        if choice == "Start Game":
            self.world = World(now)
            self.state = Mode.PLAYING
        elif choice == "Load Game":
            loaded = self._load_high_score(default=0)
            if loaded:
                self.world = World.from_save_data(loaded, now)
                self.state = Mode.PLAYING
        elif choice == "Map Editor":
            self.editor_state = EditorState()
            self.state = Mode.EDITOR
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
        if action == Action.JUMP:
            if not self.world.game_over:
                self.world.player.jump()
            else:
                self.world.reset(now)
        elif action == Action.RESTART:
            if self.world.game_over:
                self.world.reset(now)
        elif action == Action.SAVE:
            self.world.save(self.save_file, self.high_score)
        elif action == Action.LOAD:
            loaded = self._load_high_score(default=self.high_score)
            if loaded:
                self.world.merge_save_data(loaded)
        elif action == Action.MENU_BACK:
            self.state = Mode.MENU
        elif action == Action.TOGGLE_DEBUG:
            self.debug = not self.debug

    def _handle_editor_action(self, action, now):
        editor = self.editor_state
        if action == Action.PAN_UP:
            editor.pan(0, -PAN_STEP)
        elif action == Action.PAN_DOWN:
            editor.pan(0, PAN_STEP)
        elif action == Action.PAN_LEFT:
            editor.pan(-PAN_STEP, 0)
        elif action == Action.PAN_RIGHT:
            editor.pan(PAN_STEP, 0)
        elif action in SELECT_TILE_ACTIONS:
            editor.select_tile(SELECT_TILE_ACTIONS.index(action))
        elif action == Action.MENU_BACK:
            self.state = Mode.MENU

    def tick(self, keys, dt, now):
        if self.state != Mode.PLAYING:
            return
        self.world.debug = self.debug
        self.world.update(keys, dt, now)
        if self.world.game_over:
            self.high_score = max(self.high_score, self.world.score)
