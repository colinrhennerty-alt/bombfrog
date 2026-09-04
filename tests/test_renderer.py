"""Smoke tests: every draw_* function runs against a real surface without
raising. Rendering correctness itself stays a manual/visual check.
"""

import pygame
import pytest

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
from game.simulation.camera import Camera
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy
from game.simulation.explosion_effect import ExplosionEffect
from game.rendering import renderer as rendering


@pytest.fixture
def surface():
    return pygame.Surface((WIDTH, HEIGHT))


@pytest.fixture
def camera():
    return Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)


@pytest.fixture
def fonts():
    pygame.font.init()
    return pygame.font.SysFont(None, 36), pygame.font.SysFont(None, 24)


def test_draw_shadow(surface):
    rendering.draw_shadow(surface, 100, 100, base_radius=20)


def test_draw_player(surface, camera):
    rendering.draw_player(surface, Player(), camera)


def test_draw_player_jump_pose(surface, camera):
    player = Player()
    player.on_ground = False
    rendering.draw_player(surface, player, camera)


def test_draw_player_landing_pose(surface, camera):
    player = Player()
    player.land_timer = 60
    rendering.draw_player(surface, player, camera)


def test_draw_player_idle_animation_frame_and_facing_flip(surface, camera):
    player = Player()
    player.anim_index = 3
    player.facing = -1
    rendering.draw_player(surface, player, camera)
    player.facing = 1
    rendering.draw_player(surface, player, camera)


class _BlitRecordingSurface:
    """Duck-typed stand-in for pygame.Surface: real Surface.blit can't be
    monkeypatched (it's a C extension type), so this just records what it
    was asked to blit instead of a real target."""

    def __init__(self):
        self.captured = None

    def blit(self, source, dest):
        dest_rect = pygame.Rect(dest, source.get_size()) if not isinstance(dest, pygame.Rect) else dest
        self.captured = (source.get_size(), dest_rect.topleft)


def test_draw_player_blits_sprite_sized_and_positioned_to_match_the_collision_rect(camera):
    player = Player()
    fake_surface = _BlitRecordingSurface()

    rendering.draw_player(fake_surface, player, camera)

    size, topleft = fake_surface.captured
    assert size == player.rect.size
    assert topleft == camera.apply_rect(player.rect).topleft


def test_draw_enemy_draws_exactly_the_camera_translated_collision_rect(surface, camera, monkeypatch):
    enemy = Enemy("left", 500, 500)
    captured = {}
    original_rect = pygame.draw.rect

    def fake_rect(surface_, color, rect, *args, **kwargs):
        captured["rect"] = pygame.Rect(rect)
        return original_rect(surface_, color, rect, *args, **kwargs)

    monkeypatch.setattr(pygame.draw, "rect", fake_rect)
    rendering.draw_enemy(surface, enemy, camera)

    assert captured["rect"] == camera.apply_rect(enemy.rect)


def test_draw_bomb(surface, camera):
    rendering.draw_bomb(surface, Bomb(100, 100), camera)


def test_draw_bomb_subtracts_fall_offset_from_screen_y(surface, camera, monkeypatch):
    bomb = Bomb(100, 100, fall_offset=-30)
    captured = {}
    original_circle = pygame.draw.circle

    def fake_circle(surface_, color, center, *args, **kwargs):
        captured.setdefault("centers", []).append(center)
        return original_circle(surface_, color, center, *args, **kwargs)

    monkeypatch.setattr(pygame.draw, "circle", fake_circle)
    rendering.draw_bomb(surface, bomb, camera)

    expected_x, expected_y = camera.apply(bomb.x, bomb.y)
    expected_y -= bomb.fall_offset
    assert captured["centers"][0] == (int(expected_x), int(expected_y))


def test_draw_bomb_explosion_radius(surface, camera):
    rendering.draw_bomb_explosion_radius(surface, Bomb(100, 100), camera)


def test_draw_shard(surface, camera):
    rendering.draw_shard(surface, Shard(100, 100, angle=0, speed=5), camera)


def test_draw_enemy_each_type(surface, camera):
    for enemy_type in ("grunt", "heavy", "elite"):
        enemy = Enemy("left", 500, 500)
        enemy.type = enemy_type
        rendering.draw_enemy(surface, enemy, camera)


def test_draw_explosion_effect(surface, camera):
    rendering.draw_explosion_effect(surface, ExplosionEffect(100, 100, radius=140), camera)


def test_draw_scene_with_full_cast(surface, camera):
    rendering.draw_scene(
        surface,
        player=Player(),
        bombs=[Bomb(100, 100)],
        shards=[Shard(100, 100, angle=0, speed=5)],
        enemies=[Enemy("left", 500, 500)],
        effects=[ExplosionEffect(100, 100, radius=140)],
        camera=camera,
    )


def test_draw_scene_with_no_player(surface, camera):
    rendering.draw_scene(surface, player=None, bombs=[], shards=[], enemies=[], effects=[], camera=camera)


def test_draw_debug_boxes_with_full_cast(surface, camera):
    rendering.draw_debug_boxes(
        surface,
        player=Player(),
        bombs=[Bomb(100, 100)],
        shards=[Shard(100, 100, angle=0, speed=5)],
        enemies=[Enemy("left", 500, 500)],
        camera=camera,
    )


def test_draw_debug_boxes_with_no_player(surface, camera):
    rendering.draw_debug_boxes(surface, player=None, bombs=[], shards=[], enemies=[], camera=camera)


def test_draw_debug_boxes_draws_each_entitys_actual_collision_rect(surface):
    surface.fill((0, 0, 0))
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    player = Player()
    player.x, player.y = 100, 100  # comfortably inside the viewport regardless of camera clamp
    player._sync_rect()
    camera.follow(player.centerx, player.centery)
    rendering.draw_debug_boxes(surface, player=player, bombs=[], shards=[], enemies=[], camera=camera)
    # the outline is drawn exactly on the camera-translated rect: sample its border pixel
    screen_rect = camera.apply_rect(player.rect)
    color_at_top_left = surface.get_at(screen_rect.topleft)[:3]
    assert color_at_top_left != (0, 0, 0)


def test_draw_ground(surface, camera):
    rendering.draw_ground(surface, camera)


def test_draw_overlay(surface, camera):
    rendering.draw_overlay(surface, [Bomb(100, 100)], camera)


def test_draw_hud(surface, fonts):
    font, small_font = fonts
    rendering.draw_hud(surface, font, small_font, score=10, high_score=20, bombs_left=2, lives=3, bomb_cooldown=0)


def test_draw_menu(surface, fonts):
    font, small_font = fonts
    rendering.draw_menu(surface, font, small_font, ["Start Game", "Load Game", "Quit"], selected=0)


def test_draw_game_over_overlay(surface, fonts):
    font, small_font = fonts
    rendering.draw_game_over_overlay(surface, font, small_font)
