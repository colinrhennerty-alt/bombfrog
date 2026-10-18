"""Drawing the gameplay floor: grass inside the arena, stone on the border."""

from game.config import WIDTH, HEIGHT
from game.rendering.isometric_assets import get_grass_tile, get_stone_tile
from game.rendering.tile_geometry import (
    TILE_WIDTH, TILE_HEIGHT, TILE_FOOTPRINT_HEIGHT, ground_tile_screen_pos, is_border_tile, visible_tile_range,
)


def draw_ground(surface, camera):
    surface.fill((52, 88, 58))
    grass_tile = get_grass_tile()
    stone_tile = get_stone_tile()
    half_h = TILE_FOOTPRINT_HEIGHT / 2
    cam_col = camera.x / TILE_WIDTH
    cam_row = camera.y / half_h

    min_col, max_col, min_row, max_row = visible_tile_range(camera)

    # Draw in ascending-row order so a tile's diamond skirt is correctly
    # overlapped by the row in front of it (rows no longer fan diagonally,
    # but the vertical stacking/overlap still needs front-drawn-last).
    coords = sorted(
        (
            (col, row)
            for col in range(int(min_col), int(max_col))
            for row in range(int(min_row), int(max_row))
        ),
        key=lambda cr: cr[1],
    )

    for col, row in coords:
        tile = stone_tile if is_border_tile(col, row, TILE_WIDTH, half_h) else grass_tile
        # (col - cam_col) * TILE_WIDTH == col * TILE_WIDTH - camera.x, i.e.
        # exactly Camera.apply's world-to-screen mapping — no extra
        # centering term. An earlier "+ WIDTH/2 - half_w" here shifted
        # every tile ~850px from where entities actually render (masked
        # by uniform grass, but it broke alignment with the border zone).
        sx, sy = ground_tile_screen_pos(col - cam_col, row - cam_row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=row)
        if sx + TILE_WIDTH >= 0 and sx <= WIDTH and sy + TILE_HEIGHT >= 0 and sy <= HEIGHT:
            surface.blit(tile, (sx, sy))
