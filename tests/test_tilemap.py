from game.simulation.tilemap import TileMap


def test_get_tile_returns_none_for_unpainted_cell():
    tilemap = TileMap(10, 10)
    assert tilemap.get_tile(3, 4) is None


def test_set_tile_then_get_tile_round_trips():
    tilemap = TileMap(10, 10)
    tilemap.set_tile(3, 4, "tile_022")
    assert tilemap.get_tile(3, 4) == "tile_022"


def test_to_dict_includes_dimensions_and_cells():
    tilemap = TileMap(64, 32)
    tilemap.set_tile(12, 4, "tile_022")
    tilemap.set_tile(13, 4, "tile_063")

    data = tilemap.to_dict()

    assert data["width_tiles"] == 64
    assert data["height_tiles"] == 32
    assert data["cells"] == {"12,4": "tile_022", "13,4": "tile_063"}


def test_from_dict_restores_tiles_at_integer_coordinates():
    data = {
        "width_tiles": 64,
        "height_tiles": 32,
        "cells": {"12,4": "tile_022", "13,4": "tile_063"},
    }

    tilemap = TileMap.from_dict(data)

    assert tilemap.width_tiles == 64
    assert tilemap.height_tiles == 32
    assert tilemap.get_tile(12, 4) == "tile_022"
    assert tilemap.get_tile(13, 4) == "tile_063"


def test_to_dict_from_dict_round_trip_including_unpainted_cells():
    tilemap = TileMap(20, 20)
    tilemap.set_tile(0, 0, "tile_000")
    tilemap.set_tile(19, 19, "tile_114")

    restored = TileMap.from_dict(tilemap.to_dict())

    assert restored.get_tile(0, 0) == "tile_000"
    assert restored.get_tile(19, 19) == "tile_114"
    assert restored.get_tile(5, 5) is None


def test_from_dict_handles_negative_coordinates():
    data = {"width_tiles": 5, "height_tiles": 5, "cells": {"-1,-2": "tile_005"}}
    tilemap = TileMap.from_dict(data)
    assert tilemap.get_tile(-1, -2) == "tile_005"
