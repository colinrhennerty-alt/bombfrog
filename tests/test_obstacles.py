"""Tree trunks block feet: the frog and critters can't walk through a trunk,
can walk behind or in front of one, and slide along it. A stump can be
jumped; a full tree can't."""

import random

import pygame

from game.config import PLAYER_SPEED, ENEMY_SPEED, TREE_SCALE, TREE_TRUNK_DEPTH, FEET_HEIGHT
from game.simulation.enemy import Enemy
from game.simulation.obstacles import feet_rect, trunk_obstacle
from game.simulation.player import Player
from game.simulation.trees import TREE_KINDS, Tree, kind_named
from game.simulation.world import World

KEYS = (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s)


def _keys(*held):
    return {key: key in held for key in KEYS}


TREE = Tree("tree_oak_large", 2000, 1500)
STUMP = Tree("stump", 2000, 1500)


def _frog_left_of(tree, feet_y=None):
    """A grounded frog whose feet strip ends one step short of the trunk."""
    trunk = trunk_obstacle(tree).rect
    player = Player()
    feet_width = feet_rect(0, 0, player.width, player.height).width
    feet_right = trunk.x - 1
    player.x = feet_right - (player.width + feet_width) / 2
    player.y = (feet_y if feet_y is not None else tree.y) - player.height
    player._sync_rect()
    return player


def _walk(mover_update, frames):
    for _ in range(frames):
        mover_update()


# --- footprints ------------------------------------------------------------

def test_a_trunk_footprint_sits_on_the_trees_base_and_matches_its_trunk_art():
    for kind in TREE_KINDS:
        rect = trunk_obstacle(Tree(kind.name, 2000, 1500)).rect
        assert rect.centerx == 2000 and rect.centery == 1500
        assert rect.width == kind.trunk_art_px * TREE_SCALE
        assert rect.height == TREE_TRUNK_DEPTH


def test_only_stumps_can_be_jumped():
    assert kind_named("stump").jumpable
    assert not any(k.jumpable for k in TREE_KINDS if k.name != "stump")


def test_feet_are_a_thin_strip_along_the_bottom_of_the_hitbox():
    feet = feet_rect(100, 200, 54, 40)
    assert feet.height == FEET_HEIGHT
    assert feet.y + feet.height == 240
    assert feet.centerx == 100 + 54 / 2
    assert feet.width < 54


# --- the frog --------------------------------------------------------------

def test_the_frog_cannot_walk_through_a_trunk():
    obstacles = [trunk_obstacle(TREE)]
    player = _frog_left_of(TREE)
    _walk(lambda: player.update(_keys(pygame.K_RIGHT), 16, obstacles=obstacles), 30)
    assert not feet_rect(player.x, player.y, player.width, player.height).colliderect(obstacles[0].rect)
    assert player.rect.centerx < TREE.x


def test_without_obstacles_the_same_walk_goes_straight_past():
    player = _frog_left_of(TREE)
    _walk(lambda: player.update(_keys(pygame.K_RIGHT), 16), 30)
    assert player.rect.centerx > TREE.x


def test_the_frog_slides_along_a_trunk_instead_of_sticking():
    obstacles = [trunk_obstacle(TREE)]
    player = _frog_left_of(TREE)
    start_y = player.y
    _walk(lambda: player.update(_keys(pygame.K_RIGHT, pygame.K_DOWN), 16, obstacles=obstacles), 10)
    assert player.y == start_y + 10 * PLAYER_SPEED


def test_the_frog_walks_behind_a_tree_with_its_feet_above_the_trunk():
    obstacles = [trunk_obstacle(TREE)]
    trunk_top = obstacles[0].rect.y
    player = _frog_left_of(TREE, feet_y=trunk_top - 1)
    _walk(lambda: player.update(_keys(pygame.K_RIGHT), 16, obstacles=obstacles), 30)
    assert player.rect.centerx > TREE.x


def test_the_frog_walks_in_front_of_a_tree_with_its_feet_below_the_trunk():
    obstacles = [trunk_obstacle(TREE)]
    trunk_bottom = obstacles[0].rect.y + obstacles[0].rect.height
    player = _frog_left_of(TREE, feet_y=trunk_bottom + FEET_HEIGHT + 1)
    _walk(lambda: player.update(_keys(pygame.K_RIGHT), 16, obstacles=obstacles), 30)
    assert player.rect.centerx > TREE.x


def test_a_jumping_frog_still_cannot_pass_a_full_tree():
    obstacles = [trunk_obstacle(TREE)]
    player = _frog_left_of(TREE)
    player.jump()
    _walk(lambda: player.update(_keys(pygame.K_RIGHT), 16, obstacles=obstacles), 12)
    assert player.on_ground is False  # still mid-jump when it reached the trunk
    assert player.rect.centerx < TREE.x


def test_a_jumping_frog_clears_a_stump_but_a_walking_one_is_blocked():
    obstacles = [trunk_obstacle(STUMP)]
    walker = _frog_left_of(STUMP)
    _walk(lambda: walker.update(_keys(pygame.K_RIGHT), 16, obstacles=obstacles), 30)
    assert walker.rect.centerx < STUMP.x

    jumper = _frog_left_of(STUMP)
    jumper.jump()
    _walk(lambda: jumper.update(_keys(pygame.K_RIGHT), 16, obstacles=obstacles), 30)
    assert jumper.rect.centerx > STUMP.x


def test_a_frog_already_overlapping_a_trunk_can_walk_out():
    obstacles = [trunk_obstacle(TREE)]
    player = _frog_left_of(TREE)
    player.x += 20  # feet now overlap the trunk (e.g. an old save)
    player._sync_rect()
    start_x = player.x
    player.update(_keys(pygame.K_LEFT), 16, obstacles=obstacles)
    assert player.x == start_x - PLAYER_SPEED


# --- critters --------------------------------------------------------------

def _critter_left_of(tree, vx=ENEMY_SPEED):
    enemy = Enemy("left", tree.x, tree.y, rng=random.Random(1))
    trunk = trunk_obstacle(tree).rect
    feet_width = feet_rect(0, 0, enemy.width, enemy.height).width
    enemy.x = trunk.x - 1 - (enemy.width + feet_width) / 2
    enemy.y = tree.y - enemy.height
    enemy.vx, enemy.vy = vx, 0.0
    enemy._sync_rect()
    return enemy


def test_a_wandering_critter_turns_around_at_a_trunk():
    obstacles = [trunk_obstacle(TREE)]
    enemy = _critter_left_of(TREE)
    _walk(lambda: enemy.update(16, obstacles=obstacles), 5)
    assert enemy.vx < 0
    assert enemy.rect.centerx < TREE.x


def test_a_chasing_critter_slides_around_a_trunk():
    obstacles = [trunk_obstacle(TREE)]
    enemy = _critter_left_of(TREE)
    enemy.follow_rolled, enemy.following = True, True
    target = (TREE.x + 200, TREE.y + 60)  # beyond the tree, a little lower
    start_y = enemy.y
    for _ in range(80):
        enemy.update(16, target=target, obstacles=obstacles)
        assert not feet_rect(enemy.x, enemy.y, enemy.width, enemy.height).colliderect(obstacles[0].rect)
    assert enemy.y > start_y  # worked its way down the trunk's side...
    assert enemy.rect.centerx > TREE.x  # ...and got around it


def test_critters_cannot_jump_stumps():
    obstacles = [trunk_obstacle(STUMP)]
    enemy = _critter_left_of(STUMP)
    _walk(lambda: enemy.update(16, obstacles=obstacles), 5)
    assert enemy.vx < 0


# --- the round -------------------------------------------------------------

def test_a_round_turns_every_tree_into_an_obstacle():
    world = World(now=0, rng=random.Random(7))
    assert [o.rect for o in world.obstacles] == [trunk_obstacle(t).rect for t in world.trees]


def test_the_round_blocks_the_frog_at_a_trunk():
    world = World(now=0, rng=random.Random(7))
    tree = world.trees[0]
    world.player = _frog_left_of(tree)
    world.enemies = []
    for frame in range(30):
        world.update(_keys(pygame.K_RIGHT), 16, now=frame * 16)
    assert world.player.rect.centerx < tree.x
