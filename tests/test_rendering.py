"""Smoke tests: every draw_* function runs against a real surface without
raising. Rendering correctness itself stays a manual/visual check.
"""

import pygame
import pytest

from game.config import WIDTH, HEIGHT
from game.entities import Player, Bomb, Shard, Enemy, ExplosionEffect
from game import rendering


@pytest.fixture
def surface():
    return pygame.Surface((WIDTH, HEIGHT))


@pytest.fixture
def fonts():
    pygame.font.init()
    return pygame.font.SysFont(None, 36), pygame.font.SysFont(None, 24)


def test_world_scale_is_bounded():
    assert 0.8 <= rendering.world_scale(0) <= 1.2001
    assert 0.8 <= rendering.world_scale(10_000) <= 1.2001


def test_draw_shadow(surface):
    rendering.draw_shadow(surface, 100, 100, base_radius=20, scale=1.0)


def test_draw_player(surface):
    rendering.draw_player(surface, Player())


def test_draw_bomb(surface):
    rendering.draw_bomb(surface, Bomb(100, 100))


def test_draw_bomb_explosion_radius(surface):
    rendering.draw_bomb_explosion_radius(surface, Bomb(100, 100))


def test_draw_shard(surface):
    rendering.draw_shard(surface, Shard(100, 100, angle=0, speed=5))


def test_draw_enemy_each_type(surface):
    for enemy_type in ("grunt", "heavy", "elite"):
        enemy = Enemy("left")
        enemy.type = enemy_type
        rendering.draw_enemy(surface, enemy)


def test_draw_explosion_effect(surface):
    rendering.draw_explosion_effect(surface, ExplosionEffect(100, 100, radius=140))


def test_draw_scene_with_full_cast(surface):
    rendering.draw_scene(
        surface,
        player=Player(),
        bombs=[Bomb(100, 100)],
        shards=[Shard(100, 100, angle=0, speed=5)],
        enemies=[Enemy("left")],
        effects=[ExplosionEffect(100, 100, radius=140)],
    )


def test_draw_scene_with_no_player(surface):
    rendering.draw_scene(surface, player=None, bombs=[], shards=[], enemies=[], effects=[])


def test_draw_parallax_background(surface):
    rendering.draw_parallax_background(surface, cam_x=250)


def test_draw_ground(surface):
    rendering.draw_ground(surface)


def test_draw_overlay(surface):
    rendering.draw_overlay(surface, [Bomb(100, 100)])


def test_draw_hud(surface, fonts):
    font, small_font = fonts
    rendering.draw_hud(surface, font, small_font, score=10, high_score=20, bombs_left=2, lives=3, bomb_cooldown=0)


def test_draw_menu(surface, fonts):
    font, small_font = fonts
    rendering.draw_menu(surface, font, small_font, ["Start Game", "Load Game", "Quit"], selected=0)


def test_draw_game_over_overlay(surface, fonts):
    font, small_font = fonts
    rendering.draw_game_over_overlay(surface, font, small_font)
