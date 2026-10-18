import os
import random

import pytest

from game.config import TILE_WIDTH, TILE_FOOTPRINT_HEIGHT
from game.rendering.isometric_assets import TILE_DIR
from game.simulation.terrain import (
    GROUND_KINDS, MEADOW, cell_center_px, generate_ground, grid_size, neighbors,
)

ALL_KINDS = [MEADOW] + GROUND_KINDS
SEEDS = [1, 2, 3, 4, 5]


def _kind_by_tile():
    lookup = {}
    for kind in ALL_KINDS:
        for tile_id in kind.tile_ids + kind.edge_tile_ids:
            lookup[tile_id] = kind.name
    return lookup


KIND_BY_TILE = _kind_by_tile()


@pytest.fixture(scope="module")
def grounds():
    return {seed: generate_ground(random.Random(seed)) for seed in SEEDS}


def _kinds(ground):
    return {cell: KIND_BY_TILE[data["tile_id"]] for cell, data in ground.cells.items()}


def test_same_seed_makes_the_same_map(grounds):
    assert generate_ground(random.Random(SEEDS[0])).cells == grounds[SEEDS[0]].cells


def test_different_seeds_make_different_maps(grounds):
    assert grounds[1].cells != grounds[2].cells


def test_every_cell_is_set_to_a_known_flat_non_wall_tile(grounds):
    cols, rows = grid_size()
    for ground in grounds.values():
        assert set(ground.cells) == {(c, r) for c in range(cols) for r in range(rows)}
        for data in ground.cells.values():
            assert data["tile_id"] in KIND_BY_TILE
            assert data["is_wall"] is False


def test_no_patch_tile_stands_alone(grounds):
    # The user's rule: dirt (etc.) comes in patches, never a lone tile.
    for ground in grounds.values():
        kinds = _kinds(ground)
        for (col, row), kind in kinds.items():
            if kind == MEADOW.name:
                continue
            same = sum(1 for n in neighbors(col, row) if kinds[n] == kind)
            assert same >= 2, f"lone {kind} tile at {(col, row)}"


def _component_sizes(kinds, kind_name):
    remaining = {cell for cell, kind in kinds.items() if kind == kind_name}
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            cell = stack.pop()
            size += 1
            for n in neighbors(*cell):
                if n in remaining:
                    remaining.remove(n)
                    stack.append(n)
        sizes.append(size)
    return sizes


def test_patch_kinds_form_sizable_clumps_not_scatter(grounds):
    for kind in GROUND_KINDS:
        sizes = []
        for ground in grounds.values():
            sizes += _component_sizes(_kinds(ground), kind.name)
        assert sizes, f"{kind.name} never appeared"
        assert sum(sizes) / len(sizes) >= 8, f"{kind.name} patches average {sum(sizes) / len(sizes):.1f} cells"


def test_edge_tiles_only_sit_on_a_patch_rim(grounds):
    for kind in GROUND_KINDS:
        if not kind.edge_tile_ids:
            continue
        for ground in grounds.values():
            kinds = _kinds(ground)
            for (col, row), data in ground.cells.items():
                if data["tile_id"] in kind.edge_tile_ids:
                    assert any(kinds[n] != kind.name for n in neighbors(col, row))


def test_patch_interiors_use_interior_tiles(grounds):
    for kind in GROUND_KINDS:
        if not kind.edge_tile_ids:
            continue
        for ground in grounds.values():
            kinds = _kinds(ground)
            for (col, row), data in ground.cells.items():
                if kinds[(col, row)] == kind.name and all(kinds[n] == kind.name for n in neighbors(col, row)):
                    assert data["tile_id"] in kind.tile_ids


def test_every_ground_tile_id_has_art():
    for tile_id in KIND_BY_TILE:
        assert os.path.exists(os.path.join(TILE_DIR, f"{tile_id}.png")), tile_id


def test_cell_centers_follow_the_staggered_brick_grid():
    half_h = TILE_FOOTPRINT_HEIGHT / 2
    even_x, even_y = cell_center_px(3, 4)
    odd_x, odd_y = cell_center_px(3, 5)
    assert odd_x - even_x == TILE_WIDTH / 2
    assert odd_y - even_y == half_h


def test_neighbors_stay_on_the_grid():
    cols, rows = grid_size()
    for cell in [(0, 0), (cols - 1, rows - 1), (0, 1), (cols - 1, 1)]:
        for col, row in neighbors(*cell):
            assert 0 <= col < cols and 0 <= row < rows
