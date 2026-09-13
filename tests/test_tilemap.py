from game.simulation.tilemap import TileMap


def test_get_tile_returns_none_for_unpainted_cell():
    tilemap = TileMap(10, 10)
    assert tilemap.get_tile(3, 4) is None


def test_set_tile_then_get_tile_round_trips():
    tilemap = TileMap(10, 10)
    tilemap.set_tile(3, 4, "tile_022")
    assert tilemap.get_tile(3, 4) == "tile_022"


def test_is_wall_defaults_to_false_for_unpainted_cell():
    tilemap = TileMap(10, 10)
    assert tilemap.is_wall(3, 4) is False


def test_set_tile_defaults_is_wall_to_false():
    tilemap = TileMap(10, 10)
    tilemap.set_tile(3, 4, "tile_022")
    assert tilemap.is_wall(3, 4) is False


def test_set_tile_can_mark_a_cell_as_a_wall():
    tilemap = TileMap(10, 10)
    tilemap.set_tile(3, 4, "tile_022", is_wall=True)
    assert tilemap.is_wall(3, 4) is True
    assert tilemap.get_tile(3, 4) == "tile_022"  # art unaffected by wall flag


def test_set_tile_can_explicitly_clear_the_wall_flag():
    tilemap = TileMap(10, 10)
    tilemap.set_tile(3, 4, "tile_022", is_wall=True)
    tilemap.set_tile(3, 4, "tile_022", is_wall=False)
    assert tilemap.is_wall(3, 4) is False


def test_clear_empties_all_cells():
    tilemap = TileMap(10, 10)
    tilemap.set_tile(1, 1, "tile_000")
    tilemap.set_tile(2, 2, "tile_001", is_wall=True)

    tilemap.clear()

    assert tilemap.get_tile(1, 1) is None
    assert tilemap.get_tile(2, 2) is None
    assert tilemap.is_wall(2, 2) is False


def test_clear_preserves_dimensions():
    tilemap = TileMap(64, 32)
    tilemap.clear()
    assert tilemap.width_tiles == 64
    assert tilemap.height_tiles == 32


def test_to_dict_includes_dimensions_and_cells_with_tile_id_and_wall_flag():
    tilemap = TileMap(64, 32)
    tilemap.set_tile(12, 4, "tile_022")
    tilemap.set_tile(13, 4, "tile_063", is_wall=True)

    data = tilemap.to_dict()

    assert data["width_tiles"] == 64
    assert data["height_tiles"] == 32
    assert data["cells"] == {
        "12,4": {"tile_id": "tile_022", "is_wall": False},
        "13,4": {"tile_id": "tile_063", "is_wall": True},
    }


def test_from_dict_restores_tiles_and_wall_flags_at_integer_coordinates():
    data = {
        "width_tiles": 64,
        "height_tiles": 32,
        "cells": {
            "12,4": {"tile_id": "tile_022", "is_wall": False},
            "13,4": {"tile_id": "tile_063", "is_wall": True},
        },
    }

    tilemap = TileMap.from_dict(data)

    assert tilemap.width_tiles == 64
    assert tilemap.height_tiles == 32
    assert tilemap.get_tile(12, 4) == "tile_022"
    assert tilemap.is_wall(12, 4) is False
    assert tilemap.get_tile(13, 4) == "tile_063"
    assert tilemap.is_wall(13, 4) is True


def test_to_dict_from_dict_round_trip_including_unpainted_cells_and_walls():
    tilemap = TileMap(20, 20)
    tilemap.set_tile(0, 0, "tile_000")
    tilemap.set_tile(19, 19, "tile_114", is_wall=True)

    restored = TileMap.from_dict(tilemap.to_dict())

    assert restored.get_tile(0, 0) == "tile_000"
    assert restored.is_wall(0, 0) is False
    assert restored.get_tile(19, 19) == "tile_114"
    assert restored.is_wall(19, 19) is True
    assert restored.get_tile(5, 5) is None
    assert restored.is_wall(5, 5) is False


def test_from_dict_handles_negative_coordinates():
    data = {
        "width_tiles": 5,
        "height_tiles": 5,
        "cells": {"-1,-2": {"tile_id": "tile_005", "is_wall": False}},
    }
    tilemap = TileMap.from_dict(data)
    assert tilemap.get_tile(-1, -2) == "tile_005"
