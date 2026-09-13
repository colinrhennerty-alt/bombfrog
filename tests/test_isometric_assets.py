import pygame

from game.rendering.isometric_assets import get_grass_tile, get_stone_tile, get_all_tiles, TILE_WIDTH, TILE_HEIGHT


def test_get_grass_tile_returns_a_surface():
    tile = get_grass_tile()
    assert isinstance(tile, pygame.Surface)


def test_grass_tile_is_scaled_to_tile_size():
    tile = get_grass_tile()
    assert tile.get_size() == (TILE_WIDTH, TILE_HEIGHT)


def test_get_grass_tile_is_cached_across_calls():
    first = get_grass_tile()
    second = get_grass_tile()
    assert first is second


def test_get_stone_tile_returns_a_surface():
    tile = get_stone_tile()
    assert isinstance(tile, pygame.Surface)


def test_stone_tile_is_scaled_to_tile_size():
    tile = get_stone_tile()
    assert tile.get_size() == (TILE_WIDTH, TILE_HEIGHT)


def test_get_stone_tile_is_cached_across_calls():
    first = get_stone_tile()
    second = get_stone_tile()
    assert first is second


def test_stone_tile_is_a_different_image_than_grass_tile():
    assert get_stone_tile() is not get_grass_tile()


def test_get_all_tiles_includes_the_grass_and_stone_tiles():
    tiles = get_all_tiles()
    assert "tile_022" in tiles
    assert "tile_063" in tiles


def test_get_all_tiles_returns_many_tiles():
    tiles = get_all_tiles()
    assert len(tiles) > 100


def test_get_all_tiles_values_are_surfaces_scaled_to_tile_size():
    tiles = get_all_tiles()
    for tile in tiles.values():
        assert isinstance(tile, pygame.Surface)
        assert tile.get_size() == (TILE_WIDTH, TILE_HEIGHT)


def test_get_all_tiles_is_cached_across_calls():
    first = get_all_tiles()
    second = get_all_tiles()
    assert first is second
