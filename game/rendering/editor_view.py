"""Drawing the map editor: the painted tile grid with hover highlight, and
the sidebar with the palette and buttons."""

import pygame

from game.config import HEIGHT, EDITOR_SIDEBAR_WIDTH
from game.rendering.isometric_assets import get_all_tiles
from game.rendering.tile_geometry import (
    TILE_WIDTH, TILE_HEIGHT, TILE_FOOTPRINT_HEIGHT, ground_tile_screen_pos, visible_tile_range,
)


def draw_editor(surface, editor_state):
    """The map editor's ground grid and hover highlight, scoped to the
    map viewport (left of the sidebar) — see draw_editor_sidebar for the
    separate palette/buttons panel.

    Structurally parallel to draw_ground: same visible-range/tile-position
    math, but each cell looks up its own painted tile (or an empty
    placeholder) from editor_state.tilemap instead of the fixed
    grass/border rule."""
    surface.fill((30, 30, 40))
    camera = editor_state.camera
    all_tiles = get_all_tiles()
    half_h = TILE_FOOTPRINT_HEIGHT / 2
    cam_col = camera.x / TILE_WIDTH
    cam_row = camera.y / half_h

    min_col, max_col, min_row, max_row = visible_tile_range(camera)
    coords = sorted(
        (
            (col, row)
            for col in range(int(min_col), int(max_col))
            for row in range(int(min_row), int(max_row))
        ),
        key=lambda cr: cr[1],
    )

    for col, row in coords:
        sx, sy = ground_tile_screen_pos(col - cam_col, row - cam_row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=row)
        if not (sx + TILE_WIDTH >= 0 and sx <= camera.viewport_width and sy + TILE_HEIGHT >= 0 and sy <= HEIGHT):
            continue
        tile_id = editor_state.tilemap.get_tile(col, row)
        if tile_id is not None and tile_id in all_tiles:
            surface.blit(all_tiles[tile_id], (sx, sy))
        else:
            pygame.draw.rect(surface, (60, 60, 70), (sx, sy, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT), 1)
        if editor_state.tilemap.is_wall(col, row):
            pygame.draw.rect(surface, (220, 40, 40), (sx, sy, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT), 2)

    if editor_state.hover_col is not None:
        hx, hy = ground_tile_screen_pos(
            editor_state.hover_col - cam_col, editor_state.hover_row - cam_row,
            TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=editor_state.hover_row,
        )
        pygame.draw.rect(surface, (255, 255, 0), (hx, hy, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT), 2)


def draw_editor_sidebar(surface, editor_state, small_font=None):
    """The map editor's tile palette and Save/Load buttons — a fixed
    panel kept visually and logically separate from the map view
    (draw_editor), occupying the screen region right of the map's
    (already-shrunk) camera viewport."""
    all_tiles = get_all_tiles()
    sidebar_rect = (editor_state.camera.viewport_width, 0, EDITOR_SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(surface, (45, 45, 55), sidebar_rect)

    for tile_id, (x, y, w, h) in editor_state.palette_layout.items():
        thumb = pygame.transform.scale(all_tiles[tile_id], (w, h))
        surface.blit(thumb, (x, y))
        if tile_id == editor_state.selected_tile_id:
            pygame.draw.rect(surface, (255, 255, 0), (x, y, w, h), 2)

    buttons = (
        (editor_state.save_button_rect, "Save", (80, 80, 95)),
        (editor_state.load_button_rect, "Load", (80, 80, 95)),
        (editor_state.wall_mode_button_rect, "Wall Mode", (200, 70, 70) if editor_state.wall_mode else (80, 80, 95)),
        (editor_state.reset_button_rect, "Confirm?" if editor_state.reset_pending else "Reset", (200, 140, 40) if editor_state.reset_pending else (80, 80, 95)),
    )
    for rect, label, color in buttons:
        pygame.draw.rect(surface, color, rect)
        if small_font is not None:
            x, y, w, h = rect
            text = small_font.render(label, True, (240, 240, 240))
            surface.blit(text, (x + w / 2 - text.get_width() / 2, y + h / 2 - text.get_height() / 2))
