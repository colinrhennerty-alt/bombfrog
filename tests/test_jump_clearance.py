"""Gameplay guarantee: the frog can always jump over every enemy type.

Enemies only hurt a grounded frog (World._enemy_hits_player), so clearing
an enemy means crossing its whole width while airborne. These tests run
the real Player/Enemy physics rather than re-deriving the math, so any
retune of sizes, speeds, gravity or jump strength is checked for free.
"""

import random

import pygame
import pytest

from game.simulation.enemy import Enemy
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.player import Player

TICK_MS = 16


def _enemy_of_type(enemy_type):
    enemy = Enemy("left", 500, 500, rng=random.Random(0))
    enemy.type = enemy_type
    return Enemy.from_dict({**enemy.to_dict(), "type": enemy_type})


def _jump_peak_height():
    player = Player()
    player.jump()
    peak = 0
    while not player.on_ground:
        player.update({}, TICK_MS)
        peak = max(peak, -player.jump_offset)
    return peak


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_frog_jumping_head_on_clears_every_enemy_type(enemy_type):
    player = Player()
    enemy = _enemy_of_type(enemy_type)
    # Enemy approaching from the right, feet level with the frog's, its
    # near edge one pixel away — the latest possible moment to jump.
    enemy.vx = -abs(enemy.vx)
    enemy.x = player.x + player.width + 1
    enemy.y = player.y + player.height - enemy.height
    enemy._sync_rect()
    keys = {pygame.K_RIGHT: True}

    player.jump()
    while True:
        player.update(keys, TICK_MS)
        enemy.update(TICK_MS)
        assert not (player.on_ground and player.rect.colliderect(enemy.rect)), "frog landed on the enemy"
        if player.on_ground:
            break
    assert player.x > enemy.x + enemy.width, "frog landed before crossing the enemy"


@pytest.mark.parametrize("enemy_type", list(ENEMY_TYPES))
def test_frog_jump_rises_higher_than_every_enemy_is_tall(enemy_type):
    # Not a collision rule (airborne frogs never collide) but the visual
    # promise: a frog "jumping over" a stag should actually clear its antlers.
    assert _jump_peak_height() > _enemy_of_type(enemy_type).height
