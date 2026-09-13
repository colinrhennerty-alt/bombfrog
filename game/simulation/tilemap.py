"""A painted grid of tile choices, authored by the map editor.

Independent of World and its procedural grass/stone floor — this is a
plain (col, row) -> tile_id lookup with no gameplay behavior of its own.
"""


class TileMap:
    def __init__(self, width_tiles, height_tiles):
        self.width_tiles = width_tiles
        self.height_tiles = height_tiles
        self.cells = {}  # (col, row) -> tile_id string

    def set_tile(self, col, row, tile_id):
        self.cells[(col, row)] = tile_id

    def get_tile(self, col, row):
        return self.cells.get((col, row))

    def to_dict(self):
        return {
            "width_tiles": self.width_tiles,
            "height_tiles": self.height_tiles,
            # JSON object keys must be strings, so pack (col, row) as "col,row".
            "cells": {f"{col},{row}": tile_id for (col, row), tile_id in self.cells.items()},
        }

    @classmethod
    def from_dict(cls, data):
        tilemap = cls(data["width_tiles"], data["height_tiles"])
        for key, tile_id in data["cells"].items():
            col_str, row_str = key.split(",")
            tilemap.cells[(int(col_str), int(row_str))] = tile_id
        return tilemap
