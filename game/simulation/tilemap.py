"""A painted grid of tile choices, authored by the map editor.

Independent of World and its procedural grass/stone floor — this is a
plain (col, row) -> tile_id lookup with no gameplay behavior of its own.
"""


class TileMap:
    def __init__(self, width_tiles, height_tiles):
        self.width_tiles = width_tiles
        self.height_tiles = height_tiles
        self.cells = {}  # (col, row) -> {"tile_id": str, "is_wall": bool}

    def set_tile(self, col, row, tile_id, is_wall=False):
        self.cells[(col, row)] = {"tile_id": tile_id, "is_wall": is_wall}

    def get_tile(self, col, row):
        cell = self.cells.get((col, row))
        return cell["tile_id"] if cell is not None else None

    def is_wall(self, col, row):
        cell = self.cells.get((col, row))
        return cell["is_wall"] if cell is not None else False

    def clear(self):
        self.cells = {}

    def to_dict(self):
        return {
            "width_tiles": self.width_tiles,
            "height_tiles": self.height_tiles,
            # JSON object keys must be strings, so pack (col, row) as "col,row".
            "cells": {f"{col},{row}": cell for (col, row), cell in self.cells.items()},
        }

    @classmethod
    def from_dict(cls, data):
        tilemap = cls(data["width_tiles"], data["height_tiles"])
        for key, cell in data["cells"].items():
            col_str, row_str = key.split(",")
            tilemap.cells[(int(col_str), int(row_str))] = {
                "tile_id": cell["tile_id"],
                "is_wall": cell["is_wall"],
            }
        return tilemap
