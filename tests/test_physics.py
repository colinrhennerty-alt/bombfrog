import pygame

from game.config import WIDTH, GROUND_Y, GRAVITY
from game.entities import Player


def test_player_starts_on_ground():
    player = Player()
    assert player.on_ground is True
    assert player.vy == 0


def test_player_move_left_right_clamped_to_screen():
    player = Player()
    keys = {pygame.K_LEFT: True, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False}
    player.x = 0
    player.update(keys, dt=16)
    assert player.x == 0  # clamped, can't go past the left edge

    keys = {pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: True, pygame.K_d: False}
    player.x = WIDTH - player.width
    player.update(keys, dt=16)
    assert player.x == WIDTH - player.width  # clamped, can't go past the right edge


def test_player_falls_under_gravity_when_airborne():
    player = Player()
    player.on_ground = False
    player.y = 0
    keys = {pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False}
    player.update(keys, dt=16)
    assert player.vy == GRAVITY


def test_player_lands_and_resets_vertical_velocity():
    player = Player()
    player.on_ground = False
    player.y = GROUND_Y - player.height + 5
    player.vy = 10
    keys = {pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False}
    player.update(keys, dt=16)
    assert player.on_ground is True
    assert player.vy == 0
    assert player.y == GROUND_Y - player.height


def test_jump_launches_player_and_consumes_a_bomb():
    player = Player()
    bombs_before = player.bombs_left
    player.jump()
    assert player.on_ground is False
    assert player.vy < 0
    assert player.bombs_left == bombs_before - 1
    assert player.pending_bomb is True


def test_jump_does_nothing_while_airborne():
    player = Player()
    player.on_ground = False
    player.vy = -5
    bombs_before = player.bombs_left
    player.jump()
    assert player.vy == -5
    assert player.bombs_left == bombs_before


def test_jump_skips_bomb_when_out_of_bombs():
    player = Player()
    player.bombs_left = 0
    player.jump()
    assert player.pending_bomb is False


def test_pending_bomb_spawns_at_the_apex_of_the_jump():
    player = Player()
    keys = {pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False}
    player.jump()
    assert player.pending_bomb is True

    spawned_at_apex = False
    for _ in range(200):
        spawn_bomb = player.update(keys, dt=16)
        if spawn_bomb:
            spawned_at_apex = True
            break
        if player.on_ground:
            break

    assert spawned_at_apex
    assert player.pending_bomb is False


def test_explosion_outside_radius_has_no_effect():
    player = Player()
    player.x, player.y = 500, 500
    player.vx, player.vy = 0, 0
    player.on_ground = True
    player.apply_explosion(origin_x=0, origin_y=0, radius=10)
    assert player.vx == 0
    assert player.vy == 0
    assert player.on_ground is True


def test_explosion_inside_radius_launches_player_away():
    player = Player()
    player.x, player.y = 200, GROUND_Y - player.height
    player.vx, player.vy = 0, 0
    player.on_ground = True

    origin_x = player.centerx - 50
    player.apply_explosion(origin_x=origin_x, origin_y=player.centery, radius=140)

    assert player.vx > 0  # pushed away from the origin, to the right
    assert player.vy < 0  # launched upward
    assert player.on_ground is False
