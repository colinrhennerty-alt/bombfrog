import pygame

from game.rendering.isometric_assets import get_grass_tile, get_stone_tile, get_all_tiles
from game.rendering.tile_geometry import TILE_WIDTH, TILE_HEIGHT, TILE_FOOTPRINT_HEIGHT, ground_tile_screen_pos


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
    assert "floor_grass_01" in tiles
    assert "floor_stone_01" in tiles


GRIDWRIGHT_MATERIALS = (
    "grass", "autumn", "snow", "dirt", "soil", "sand", "stone", "cobble", "brick", "planks", "dungeon",
)


def test_get_all_tiles_has_three_floors_per_material():
    tiles = get_all_tiles()
    for material in GRIDWRIGHT_MATERIALS:
        for n in (1, 2, 3):
            assert f"floor_{material}_{n:02d}" in tiles


def test_floor_tiles_cover_the_staggered_grid_without_gaps():
    # Why TILE_FOOTPRINT_HEIGHT == TILE_HEIGHT: laid out by
    # ground_tile_screen_pos, the diamonds interlock into solid floor.
    tile = get_grass_tile()
    cols, rows = 4, 8
    canvas = pygame.Surface((cols * TILE_WIDTH + TILE_WIDTH, rows * TILE_FOOTPRINT_HEIGHT), pygame.SRCALPHA)
    for row in range(rows):
        for col in range(cols + 1):
            canvas.blit(tile, ground_tile_screen_pos(col, row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=row))
    # Away from the patch's own ragged outer edge, every pixel is floor.
    for y in range(TILE_FOOTPRINT_HEIGHT, (rows - 1) * TILE_FOOTPRINT_HEIGHT // 2):
        for x in range(TILE_WIDTH, cols * TILE_WIDTH):
            assert canvas.get_at((x, y)).a == 255, (x, y)


def test_get_all_tiles_values_are_surfaces_scaled_to_tile_size():
    tiles = get_all_tiles()
    for tile in tiles.values():
        assert isinstance(tile, pygame.Surface)
        assert tile.get_size() == (TILE_WIDTH, TILE_HEIGHT)


def test_get_all_tiles_is_cached_across_calls():
    first = get_all_tiles()
    second = get_all_tiles()
    assert first is second
