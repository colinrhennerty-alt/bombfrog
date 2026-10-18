"""How big each character *reads* on screen: solid (fully opaque) drawn
pixels, which ignores transparent padding and the critters' baked
semi-transparent shadows. Height alone misleads — the stag is mostly
legs and antlers, the boar a solid block — so the size ladder is checked
on what's actually drawn."""

import random

import pygame
import pytest

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, BOMB_FUSE_MS
from game.rendering import entities
from game.rendering.assets import get_critter_frames
from game.simulation.bomb import Bomb
from game.simulation.camera import Camera
from game.simulation.enemy import Enemy
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.player import Player

FULLY_OPAQUE = 254  # mask threshold: alpha > 254


@pytest.fixture
def camera():
    return Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)


def _solid_pixels(draw):
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    draw(surface)
    return pygame.mask.from_surface(surface, FULLY_OPAQUE).count()


def _frog_solid_pixels(camera):
    player = Player()
    player.x, player.y = camera.x + 100, camera.y + 100
    player._sync_rect()
    return _solid_pixels(lambda s: entities.draw_player(s, player, camera))


def _enemy_solid_pixels(enemy_type, camera):
    """Averaged over the whole walk cycle, since poses vary a little."""
    enemy = Enemy.from_dict(
        {"x": camera.x + 100, "y": camera.y + 100, "vx": 2.2, "type": enemy_type, "dead": False}
    )
    frame_count = len(get_critter_frames()[ENEMY_TYPES[enemy_type].sprite]["SE"])
    total = 0
    for index in range(frame_count):
        enemy.anim_index = index
        total += _solid_pixels(lambda s: entities.draw_enemy(s, enemy, camera))
    return total / frame_count


def test_characters_read_bigger_up_the_ladder_frog_badger_boar_stag(camera):
    sizes = [_frog_solid_pixels(camera)] + [_enemy_solid_pixels(t, camera) for t in ("grunt", "heavy", "elite")]
    assert sizes == sorted(sizes) and len(set(sizes)) == len(sizes), sizes


def test_the_stag_reads_clearly_biggest(camera):
    # "Clearly": a margin over the runner-up, not a photo finish.
    others = [_enemy_solid_pixels(t, camera) for t in ("grunt", "heavy")]
    assert _enemy_solid_pixels("elite", camera) >= 1.25 * max(others)


def _frog_and_bomb_at_its_feet(camera):
    """Bombs land at the frog's feet and the camera follows the frog, so
    compare them where they actually meet on screen."""
    player = Player()
    camera.snap_to(player.centerx, player.centery)
    bomb = Bomb(player.centerx, player.y + player.height)
    bomb.timer = 0  # fuse ring fully spent: measure the bomb itself
    return player, bomb


def test_the_bomb_reads_slightly_smaller_than_the_frog(camera):
    player, bomb = _frog_and_bomb_at_its_feet(camera)
    frog = _solid_pixels(lambda s: entities.draw_player(s, player, camera))
    bomb_pixels = _solid_pixels(lambda s: entities.draw_bomb(s, bomb, camera))
    assert 0.7 * frog <= bomb_pixels <= 0.95 * frog, (bomb_pixels, frog)


def test_the_bomb_with_its_full_fuse_ring_is_no_wider_than_the_frog(camera):
    player, bomb = _frog_and_bomb_at_its_feet(camera)
    bomb.timer = BOMB_FUSE_MS
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    entities.draw_bomb(surface, bomb, camera)
    assert surface.get_bounding_rect(min_alpha=1).width <= player.width


def test_a_grounded_bombs_shadow_is_no_wider_than_the_bomb(camera, monkeypatch):
    _, bomb = _frog_and_bomb_at_its_feet(camera)
    drawn = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    entities.draw_bomb(drawn, bomb, camera)
    bomb_width = drawn.get_bounding_rect(min_alpha=1).width

    shadows = []
    real_draw_shadow = entities.draw_shadow
    monkeypatch.setattr(entities, "draw_shadow", lambda *a, **k: shadows.append(real_draw_shadow(*a, **k)))
    shadow_only = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    monkeypatch.setattr(entities, "draw_bomb", lambda *a, **k: None)
    entities.draw_scene(shadow_only, player=None, bombs=[bomb], shards=[], enemies=[], effects=[], camera=camera)

    assert shadows, "expected the bomb to cast a shadow"
    assert shadow_only.get_bounding_rect(min_alpha=1).width <= bomb_width
