import math
import os
import random

import pytest

from game.config import (
    WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, TREE_BORDER_MARGIN, TREE_SPAWN_CLEARANCE, TREE_MIN_SPACING,
    TREE_GROVES, TREES_PER_GROVE,
)
from game.paths import resource_path
from game.simulation.player import Player
from game.simulation.terrain import GROUND_KINDS, cell_at_px, cell_center_px, generate_ground
from game.simulation.trees import TREE_KINDS, generate_trees

SEEDS = [1, 2, 3, 4, 5, 6, 7, 8]
TILLED_TILES = next(kind for kind in GROUND_KINDS if kind.name == "tilled").tile_ids


def _round(seed):
    rng = random.Random(seed)
    ground = generate_ground(rng)
    return ground, generate_trees(rng, ground)


@pytest.fixture(scope="module")
def rounds():
    return {seed: _round(seed) for seed in SEEDS}


def test_same_seed_plants_the_same_trees(rounds):
    assert _round(SEEDS[0])[1] == rounds[SEEDS[0]][1]


def test_different_seeds_plant_different_trees(rounds):
    assert rounds[1][1] != rounds[2][1]


def test_tree_count_stays_within_the_grove_limits(rounds):
    max_trees = TREE_GROVES[1] * TREES_PER_GROVE[1]
    for _, trees in rounds.values():
        assert TREE_GROVES[0] <= len(trees) <= max_trees


def test_a_round_averages_sparse_groves_not_a_forest(rounds):
    # The user's density pick: roughly 40-60 trees across the arena.
    average = sum(len(trees) for _, trees in rounds.values()) / len(rounds)
    assert 35 <= average <= 65


def test_no_tree_stands_in_or_near_the_stone_border(rounds):
    edge = WORLD_BORDER + TREE_BORDER_MARGIN
    for _, trees in rounds.values():
        for tree in trees:
            assert edge <= tree.x <= WORLD_WIDTH - edge
            assert edge <= tree.y <= WORLD_HEIGHT - edge


def test_the_frogs_spawn_point_is_left_clear(rounds):
    spawn = Player()
    for _, trees in rounds.values():
        for tree in trees:
            assert math.dist((tree.x, tree.y), (spawn.centerx, spawn.centery)) >= TREE_SPAWN_CLEARANCE


def test_trees_keep_their_spacing(rounds):
    for _, trees in rounds.values():
        for i, a in enumerate(trees):
            for b in trees[i + 1:]:
                assert math.dist((a.x, a.y), (b.x, b.y)) >= TREE_MIN_SPACING


def test_no_tree_grows_on_tilled_soil(rounds):
    for ground, trees in rounds.values():
        for tree in trees:
            assert ground.get_tile(*cell_at_px(tree.x, tree.y)) not in TILLED_TILES


def test_trees_come_in_clumps(rounds):
    # Groves, not an even scatter: most trees have a neighbor within a grove's reach.
    for _, trees in rounds.values():
        clumped = sum(
            1 for a in trees
            if any(a is not b and math.dist((a.x, a.y), (b.x, b.y)) <= TREE_MIN_SPACING * 3 for b in trees)
        )
        assert clumped / len(trees) >= 0.6


def test_rare_kinds_are_rarer_than_green_ones(rounds):
    counts = {kind.name: 0 for kind in TREE_KINDS}
    for _, trees in rounds.values():
        for tree in trees:
            counts[tree.kind] += 1
    assert counts["tree_dead"] < counts["tree_oak_large"]
    assert counts["tree_oak_blossom"] < counts["tree_oak_large"]


def test_every_tree_kind_has_art():
    for kind in TREE_KINDS:
        assert os.path.exists(resource_path(f"assets/gridwright/trees/{kind.name}.png")), kind.name


def test_cell_at_px_inverts_cell_center_px():
    for cell in [(0, 0), (3, 4), (3, 5), (40, 101)]:
        assert cell_at_px(*cell_center_px(*cell)) == cell


def test_every_tree_kinds_shadow_sprite_is_shipped():
    import json

    with open(resource_path("assets/gridwright/isometric.json"), encoding="utf-8") as f:
        sprites = json.load(f)["sprites"]
    for kind in TREE_KINDS:
        shadow = sprites[kind.name]["shadow"]
        assert os.path.exists(resource_path(f"assets/gridwright/shadows/{shadow}.png")), shadow
