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


def test_draw_shadow_shrinks_with_height_offset(surface):
    # height_offset represents how far above the ground the entity is
    # (same magnitude convention as jump_offset/fall_offset — 0 is grounded).
    # The shadow should shrink and fade as height increases, since that's
    # the depth cue that sells verticality.
    grounded = rendering.shadow_size_for(base_radius=20, height_offset=0)
    airborne = rendering.shadow_size_for(base_radius=20, height_offset=80)
    assert airborne < grounded


def test_draw_shadow_accepts_height_offset(surface):
    rendering.draw_shadow(surface, 100, 100, base_radius=20, height_offset=80)


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


def test_draw_player_moves_up_the_screen_while_airborne(camera):
    # jump_offset accumulates negative while rising (Player._apply_jump_physics
    # adds a negative vy each tick) — the drawn sprite must move to a smaller
    # screen y (up), not a larger one (down), as it climbs.
    player = Player()
    player.on_ground = False
    player.jump_offset = -50
    fake_surface = _BlitRecordingSurface()

    rendering.draw_player(fake_surface, player, camera)

    _, topleft = fake_surface.captured
    grounded_y = camera.apply_rect(player.rect).topleft[1]
    assert topleft[1] < grounded_y


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


def test_draw_bomb_draws_above_ground_while_falling(surface, camera, monkeypatch):
    # fall_offset is negative while the bomb is above the ground (it's seeded
    # from the player's jump_offset, which uses the same convention) — the
    # drawn position must be a smaller screen y (up), not larger (down).
    bomb = Bomb(100, 100, fall_offset=-30)
    captured = {}
    original_circle = pygame.draw.circle

    def fake_circle(surface_, color, center, *args, **kwargs):
        captured.setdefault("centers", []).append(center)
        return original_circle(surface_, color, center, *args, **kwargs)

    monkeypatch.setattr(pygame.draw, "circle", fake_circle)
    rendering.draw_bomb(surface, bomb, camera)

    ground_x, ground_y = camera.apply(bomb.x, bomb.y)
    drawn_x, drawn_y = captured["centers"][0]
    assert drawn_x == int(ground_x)
    assert drawn_y < ground_y


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


def test_draw_scene_shrinks_airborne_players_shadow(surface, camera, monkeypatch):
    # draw_scene must read the player's jump_offset and the bomb's
    # fall_offset and pass them into draw_shadow, not always draw a
    # grounded-size shadow.
    player = Player()
    player.jump_offset = -90
    bomb = Bomb(300, 300, fall_offset=-90)

    captured_offsets = []
    original_shadow = rendering.draw_shadow

    def fake_shadow(surface_, x, y, base_radius, height_offset=0):
        captured_offsets.append(height_offset)
        return original_shadow(surface_, x, y, base_radius, height_offset)

    monkeypatch.setattr(rendering, "draw_shadow", fake_shadow)
    rendering.draw_scene(surface, player=player, bombs=[bomb], shards=[], enemies=[], effects=[], camera=camera)

    assert -90 in captured_offsets


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


def test_ground_line_color_darkens_away_from_the_horizon():
    # The horizon is the vertical center of the viewport (HEIGHT / 2) — lines
    # there should be lightest, lines further from it (top/bottom edges)
    # should be darker, to imply the ground plane receding into the distance.
    horizon_color = rendering.ground_line_color_for(HEIGHT / 2)
    edge_color = rendering.ground_line_color_for(0)
    assert edge_color < horizon_color


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
