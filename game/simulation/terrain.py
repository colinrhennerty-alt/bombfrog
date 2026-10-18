"""Procedural ground: a meadow with patches of other flat, walkable tiles.

Each patch is a few overlapping circles, measured in world pixels (rows are
only TILE_FOOTPRINT_HEIGHT / 2 apart while columns are TILE_WIDTH apart, so
circles in tile units would come out squashed). A cleanup pass then reverts
any patch tile with fewer than two same-kind neighbors, so patches never
leave lone tiles behind.

Like ENEMY_TYPES, a new kind of patch is one entry in GROUND_KINDS. The
result is a plain TileMap (the editor's format), purely cosmetic: nothing
here blocks movement.
"""

from dataclasses import dataclass
from typing import Tuple

from game.config import WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT
from game.simulation.tilemap import TileMap

ROW_HEIGHT = TILE_FOOTPRINT_HEIGHT / 2


def _floors(material):
    """The three Gridwright floor variants of one material."""
    return tuple(f"floor_{material}_{n:02d}" for n in (1, 2, 3))


@dataclass(frozen=True)
class GroundKind:
    name: str
    tile_ids: Tuple[str, ...]
    patch_count: Tuple[int, int] = (0, 0)
    radius_px: Tuple[float, float] = (0, 0)
    # Used instead of tile_ids on a patch's rim (any neighbor of another kind).
    edge_tile_ids: Tuple[str, ...] = ()


MEADOW = GroundKind("meadow", _floors("grass"))

# Paint order: later kinds paint over earlier ones where patches overlap.
GROUND_KINDS = [
    GroundKind("autumn", _floors("autumn"), patch_count=(7, 10), radius_px=(110, 220)),
    GroundKind("dirt", _floors("dirt"), patch_count=(8, 12), radius_px=(70, 150)),
    GroundKind("tilled", _floors("soil"), patch_count=(1, 2), radius_px=(120, 200)),
]

CIRCLES_PER_PATCH = (3, 6)
CIRCLE_SPREAD = 0.9  # how far a patch's extra circles sit from its center, x radius
# Each cell's distance test is scaled by up to +-EDGE_JITTER, roughing up
# the circles' outlines (the straggler cleanup then trims the stray specks).
EDGE_JITTER = 0.2
MIN_SAME_KIND_NEIGHBORS = 2


def grid_size():
    """(cols, rows) of the world's ground grid; matches the editor's TileMap."""
    return int(WORLD_WIDTH / TILE_WIDTH), int(WORLD_HEIGHT / ROW_HEIGHT)


def cell_center_px(col, row):
    """World-pixel center of a ground cell; odd rows sit half a tile right
    (the brick-course stagger in game.rendering.tile_geometry)."""
    stagger = TILE_WIDTH / 2 if row % 2 else 0
    return col * TILE_WIDTH + stagger + TILE_WIDTH / 2, row * ROW_HEIGHT + ROW_HEIGHT / 2


def neighbors(col, row):
    """The 8 cells around (col, row) in the staggered grid, clipped to the
    grid: left/right in the same row, straight up/down two rows, and the
    four diamonds sharing an edge in the rows just above and below."""
    cols, rows = grid_size()
    diagonal_cols = (col, col + 1) if row % 2 else (col - 1, col)
    candidates = [(col - 1, row), (col + 1, row), (col, row - 2), (col, row + 2)]
    candidates += [(c, r) for r in (row - 1, row + 1) for c in diagonal_cols]
    return [(c, r) for c, r in candidates if 0 <= c < cols and 0 <= r < rows]


def generate_ground(rng):
    cols, rows = grid_size()
    kinds = {(c, r): MEADOW for c in range(cols) for r in range(rows)}
    for kind in GROUND_KINDS:
        for _ in range(rng.randint(*kind.patch_count)):
            _paint_patch(kinds, kind, rng, cols, rows)
    _remove_stragglers(kinds)

    ground = TileMap(cols, rows)
    for (col, row), kind in kinds.items():
        on_rim = kind.edge_tile_ids and any(kinds[n] is not kind for n in neighbors(col, row))
        choices = kind.edge_tile_ids if on_rim else kind.tile_ids
        ground.set_tile(col, row, rng.choice(choices))
    return ground


def _paint_patch(kinds, kind, rng, cols, rows):
    # Centers stay inside the playable area so patches aren't hidden under the stone border.
    center_x = rng.uniform(WORLD_BORDER, WORLD_WIDTH - WORLD_BORDER)
    center_y = rng.uniform(WORLD_BORDER, WORLD_HEIGHT - WORLD_BORDER)
    base_radius = rng.uniform(*kind.radius_px)
    for i in range(rng.randint(*CIRCLES_PER_PATCH)):
        spread = 0 if i == 0 else base_radius * CIRCLE_SPREAD
        x = center_x + rng.uniform(-spread, spread)
        y = center_y + rng.uniform(-spread, spread)
        radius = rng.uniform(*kind.radius_px)
        _paint_circle(kinds, kind, x, y, radius, cols, rows, rng)


def _paint_circle(kinds, kind, x, y, radius, cols, rows, rng):
    # Only scan the cells in the circle's bounding box.
    min_col = max(0, int((x - radius) / TILE_WIDTH) - 1)
    max_col = min(cols - 1, int((x + radius) / TILE_WIDTH) + 1)
    min_row = max(0, int((y - radius) / ROW_HEIGHT) - 1)
    max_row = min(rows - 1, int((y + radius) / ROW_HEIGHT) + 1)
    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            cx, cy = cell_center_px(col, row)
            reach = radius * (1 + rng.uniform(-EDGE_JITTER, EDGE_JITTER))
            if (cx - x) ** 2 + (cy - y) ** 2 <= reach ** 2:
                kinds[(col, row)] = kind


def _remove_stragglers(kinds):
    """Revert patch cells with too few same-kind neighbors to meadow,
    repeating until stable (a revert can strand the cell next to it)."""
    candidates = {cell for cell, kind in kinds.items() if kind is not MEADOW}
    while candidates:
        stranded = {
            cell for cell in candidates
            if kinds[cell] is not MEADOW
            and sum(1 for n in neighbors(*cell) if kinds[n] is kinds[cell]) < MIN_SAME_KIND_NEIGHBORS
        }
        for cell in stranded:
            kinds[cell] = MEADOW
        candidates = {n for cell in stranded for n in neighbors(*cell)}
