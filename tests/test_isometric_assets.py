import pygame

from game.rendering.isometric_assets import get_grass_tile, get_stone_tile, TILE_WIDTH, TILE_HEIGHT


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
