from game.simulation.tilemap import TileMap
from game.persistence.level_io import save_level, load_level


def test_load_level_returns_none_when_file_missing(tmp_path):
    missing_file = tmp_path / "does-not-exist.json"
    assert load_level(str(missing_file)) is None


def test_save_and_load_round_trip(tmp_path):
    save_path = tmp_path / "level.json"
    tilemap = TileMap(64, 32)
    tilemap.set_tile(12, 4, "tile_022")
    tilemap.set_tile(13, 4, "tile_063")

    save_level(str(save_path), tilemap)
    loaded = load_level(str(save_path))

    assert loaded.width_tiles == 64
    assert loaded.height_tiles == 32
    assert loaded.get_tile(12, 4) == "tile_022"
    assert loaded.get_tile(13, 4) == "tile_063"


def test_save_creates_missing_parent_directory(tmp_path):
    save_path = tmp_path / "levels" / "level.json"
    tilemap = TileMap(4, 4)

    save_level(str(save_path), tilemap)

    assert save_path.exists()
