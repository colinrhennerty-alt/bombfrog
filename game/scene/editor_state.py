"""Owns the map editor's state: a free camera over the world tile grid,
the tile palette, and the TileMap being painted.

Analogous to how World owns one round's playing-state — kept separate
since editing has no per-frame simulation to advance, just discrete
pan/select/paint/save/load actions.
"""

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, EDITOR_SIDEBAR_WIDTH
from game.simulation.camera import Camera
from game.simulation.tilemap import TileMap
from game.rendering.isometric_assets import get_all_tiles, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT
from game.rendering.renderer import screen_pos_to_tile
from game.persistence.level_io import save_level, load_level

PAN_STEP = 32

PALETTE_MARGIN = 8
PALETTE_CELL_SIZE = 32
PALETTE_COLUMNS = 6
BUTTON_HEIGHT = 32
BUTTON_GAP = 8


def _point_in_rect(x, y, rect):
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


class EditorState:
    def __init__(self, viewport_width=WIDTH, viewport_height=HEIGHT):
        width_tiles = int(WORLD_WIDTH / TILE_WIDTH)
        height_tiles = int(WORLD_HEIGHT / (TILE_FOOTPRINT_HEIGHT / 2))
        self.tilemap = TileMap(width_tiles, height_tiles)
        self.sidebar_x = viewport_width - EDITOR_SIDEBAR_WIDTH
        map_viewport_width = viewport_width - EDITOR_SIDEBAR_WIDTH
        self.camera = Camera(map_viewport_width, viewport_height, WORLD_WIDTH, WORLD_HEIGHT)
        self.palette = sorted(get_all_tiles().keys())
        self.selected_index = 0
        self.hover_col = None
        self.hover_row = None
        self.is_dragging = False
        self.wall_mode = False
        self.reset_pending = False
        self.palette_layout = self._build_palette_layout()
        (
            self.save_button_rect,
            self.load_button_rect,
            self.wall_mode_button_rect,
            self.reset_button_rect,
        ) = self._build_button_rects()

    def _build_palette_layout(self):
        layout = {}
        for i, tile_id in enumerate(self.palette):
            col, row = i % PALETTE_COLUMNS, i // PALETTE_COLUMNS
            x = self.sidebar_x + PALETTE_MARGIN + col * PALETTE_CELL_SIZE
            y = PALETTE_MARGIN + row * PALETTE_CELL_SIZE
            layout[tile_id] = (x, y, PALETTE_CELL_SIZE - 4, PALETTE_CELL_SIZE - 4)
        return layout

    def _build_button_rects(self):
        palette_rows = (len(self.palette) + PALETTE_COLUMNS - 1) // PALETTE_COLUMNS
        buttons_top = PALETTE_MARGIN + palette_rows * PALETTE_CELL_SIZE + BUTTON_GAP
        button_width = EDITOR_SIDEBAR_WIDTH - 2 * PALETTE_MARGIN
        button_x = self.sidebar_x + PALETTE_MARGIN
        rects = [
            (button_x, buttons_top + i * (BUTTON_HEIGHT + BUTTON_GAP), button_width, BUTTON_HEIGHT)
            for i in range(4)
        ]
        return tuple(rects)

    @property
    def selected_tile_id(self):
        return self.palette[self.selected_index]

    def pan(self, dx, dy):
        self.camera.x += dx
        self.camera.y += dy
        self.camera._clamp_to_bounds()

    def select_tile(self, index):
        if 0 <= index < len(self.palette):
            self.selected_index = index

    def set_hover(self, screen_x, screen_y):
        self.hover_col, self.hover_row = screen_pos_to_tile(screen_x, screen_y, self.camera)

    def paint_at_screen(self, screen_x, screen_y):
        col, row = screen_pos_to_tile(screen_x, screen_y, self.camera)
        self.tilemap.set_tile(col, row, self.selected_tile_id, is_wall=self.wall_mode)

    def point_is_in_sidebar(self, screen_x, screen_y):
        return screen_x >= self.camera.viewport_width

    def handle_sidebar_click(self, screen_x, screen_y):
        """Hit-tests a click against the sidebar's controls (palette
        tiles, Save/Load, Wall Mode, Reset). Returns "select" (selection
        already applied), "save", "load", "toggle_wall_mode",
        "reset_pending", "reset_confirmed", or None if the click hit
        nothing.

        Any recognized-control click other than a second Reset click
        cancels a pending reset rather than leaving it armed — so a
        later, unrelated click on the (now un-highlighted) Reset button
        can't accidentally land as the "confirm" half of an earlier,
        forgotten arm."""
        if _point_in_rect(screen_x, screen_y, self.reset_button_rect):
            return self._handle_reset_click()

        result = self._handle_other_control_click(screen_x, screen_y)
        if result is not None:
            self.reset_pending = False
        return result

    def _handle_reset_click(self):
        if self.reset_pending:
            self.tilemap.clear()
            self.reset_pending = False
            return "reset_confirmed"
        self.reset_pending = True
        return "reset_pending"

    def _handle_other_control_click(self, screen_x, screen_y):
        if _point_in_rect(screen_x, screen_y, self.save_button_rect):
            return "save"
        if _point_in_rect(screen_x, screen_y, self.load_button_rect):
            return "load"
        if _point_in_rect(screen_x, screen_y, self.wall_mode_button_rect):
            self.wall_mode = not self.wall_mode
            return "toggle_wall_mode"
        for tile_id, rect in self.palette_layout.items():
            if _point_in_rect(screen_x, screen_y, rect):
                self.selected_index = self.palette.index(tile_id)
                return "select"
        return None

    def save(self, path):
        save_level(path, self.tilemap)

    def load(self, path):
        loaded = load_level(path)
        if loaded is not None:
            self.tilemap = loaded
