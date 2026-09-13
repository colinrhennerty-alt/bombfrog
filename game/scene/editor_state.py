"""Owns the map editor's state: a free camera over the world tile grid,
the tile palette, and the TileMap being painted.

Analogous to how World owns one round's playing-state — kept separate
since editing has no per-frame simulation to advance, just discrete
pan/select/paint/save/load actions.
"""

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
from game.simulation.camera import Camera
from game.simulation.tilemap import TileMap
from game.rendering.isometric_assets import get_all_tiles, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT
from game.rendering.renderer import screen_pos_to_tile
from game.persistence.level_io import save_level, load_level

PAN_STEP = 32


class EditorState:
    def __init__(self, viewport_width=WIDTH, viewport_height=HEIGHT):
        width_tiles = int(WORLD_WIDTH / TILE_WIDTH)
        height_tiles = int(WORLD_HEIGHT / (TILE_FOOTPRINT_HEIGHT / 2))
        self.tilemap = TileMap(width_tiles, height_tiles)
        self.camera = Camera(viewport_width, viewport_height, WORLD_WIDTH, WORLD_HEIGHT)
        self.palette = sorted(get_all_tiles().keys())
        self.selected_index = 0
        self.hover_col = None
        self.hover_row = None

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
        self.tilemap.set_tile(col, row, self.selected_tile_id)

    def save(self, path):
        save_level(path, self.tilemap)

    def load(self, path):
        loaded = load_level(path)
        if loaded is not None:
            self.tilemap = loaded
