"""Ground-tile grid math: where a tile is drawn on screen, which tile is
under a screen point, which tiles are visible, and which are border.

Pure arithmetic, no pygame, so the map editor's state (game.scene) can use
it without depending on any drawing code.
"""

from game.config import (
    WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, TILE_WIDTH, TILE_HEIGHT, TILE_FOOTPRINT_HEIGHT,
)


def ground_tile_screen_pos(col, row, tile_width, tile_height, world_row):
    """A tile's (col, row) grid coordinate to its screen-space top-left
    offset. Straight scroll, not true isometric fan-out: col only ever
    moves screen_x and row only ever moves screen_y, matching how
    Camera.apply maps world x/y to screen x/y for every other entity.
    (An earlier true-isometric version mixed col and row into both axes,
    which made straight up/down/left/right movement look rotated 45
    degrees on the tiled ground while everything else moved straight.)

    Rows are packed at half the tile's footprint height and staggered by
    half a tile width on odd rows (brick-course layout) — the diamond
    art needs this overlap/interlock to read as a continuous floor
    instead of stacking with visible gaps or double-covered seams. The
    stagger is keyed off world_row (the tile's absolute integer grid
    row), not the camera-relative `row`, so it stays fixed to the world
    grid and doesn't flicker as the camera scrolls smoothly."""
    stagger = (tile_width / 2) if world_row % 2 else 0
    return col * tile_width + stagger, row * (tile_height / 2)


def is_border_tile(col, row, tile_width, half_h):
    """Whether a (col, row) ground tile falls in the world's impassable
    stone border zone (see WORLD_BORDER / Player/Enemy's movement
    clamping) rather than the playable interior."""
    border_cols = WORLD_BORDER / tile_width
    border_rows = WORLD_BORDER / half_h
    max_col = WORLD_WIDTH / tile_width
    max_row = WORLD_HEIGHT / half_h
    return (
        col < border_cols
        or col >= max_col - border_cols
        or row < border_rows
        or row >= max_row - border_rows
    )


def screen_pos_to_tile(screen_x, screen_y, camera):
    """Inverse of ground_tile_screen_pos: given a screen-space point (e.g.
    a mouse click) and the camera, recover the (col, row) of the ground
    tile drawn under it.

    Row inverts directly (row placement never staggers). Col depends on
    that row's stagger, which itself depends on the row — so row must be
    resolved first, then col computed against that row's own offset."""
    half_h = TILE_FOOTPRINT_HEIGHT / 2
    cam_col = camera.x / TILE_WIDTH
    cam_row = camera.y / half_h

    row = int(screen_y / half_h + cam_row)
    stagger = (TILE_WIDTH / 2) if row % 2 else 0
    col = int((screen_x - stagger) / TILE_WIDTH + cam_col)
    return col, row


def visible_tile_range(camera):
    """Which (col, row) tile grid range the camera can currently see,
    clamped to the world's own tile bounds so the ground never tiles past
    where the player could ever actually go.

    ground_tile_screen_pos places col=cam_col/row=cam_row at screen (0, 0)
    and scrolls at 1px per world-unit (matching Camera.apply exactly, no
    extra centering term) — so the screen's visible range [0, WIDTH] maps
    to col in [cam_col, cam_col + WIDTH/TILE_WIDTH], not a range centered
    on cam_col. Padding beyond that range is explained inline below."""
    half_w, half_h = TILE_WIDTH / 2, TILE_FOOTPRINT_HEIGHT / 2
    cam_col = camera.x / TILE_WIDTH
    cam_row = camera.y / half_h

    # Padding needs to cover: the brick stagger, which can shift an odd
    # row's tiles by half_w (0.5 col-units) either side of where an
    # unstaggered grid would put them; plus a couple of whole tiles of
    # safety margin so int() truncation and the diamond's own footprint
    # bleeding past its nominal cell never leave a gap at the viewport
    # edge (this was previously computed as int(half_w / TILE_WIDTH),
    # which truncates to 0 and produced visible gaps in ~45% of camera
    # positions — read as "the screen flickers a lot while moving").
    pad_cols = 1 + 2
    pad_rows = 1 + 2

    max_world_col = WORLD_WIDTH / TILE_WIDTH
    max_world_row = WORLD_HEIGHT / half_h

    min_col = max(0, int(cam_col) - pad_cols)
    max_col = min(max_world_col, int(cam_col) + WIDTH / TILE_WIDTH + pad_cols)
    min_row = max(0, int(cam_row) - pad_rows)
    max_row = min(max_world_row, int(cam_row) + HEIGHT / half_h + pad_rows)
    return min_col, max_col, min_row, max_row
