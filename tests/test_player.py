import pygame

from game.config import WIDTH, GRAVITY, DEPTH_SPEED
from game.simulation.depth import ground_y_for_depth, margin_for_depth, scale_for_depth
from game.simulation.player import Player

NO_MOVE_KEYS = {
    pygame.K_LEFT: False, pygame.K_a: False, pygame.K_RIGHT: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False,
}


def _keys(overrides):
    keys = dict(NO_MOVE_KEYS)
    keys.update(overrides)
    return keys


def test_player_starts_on_ground():
    player = Player()
    assert player.on_ground is True
    assert player.vy == 0


def test_player_spawns_at_default_depth_with_matching_ground_and_scale():
    player = Player()
    assert player.depth == 0.55
    assert player.ground_y == ground_y_for_depth(0.55)
    assert player.scale == scale_for_depth(0.55)
    assert player.y == player.ground_y - player.height


def test_player_move_left_right_clamped_to_screen():
    player = Player()
    margin = margin_for_depth(player.depth)

    player.x = 0
    player.update(_keys({pygame.K_LEFT: True}), dt=16)
    assert player.x == margin  # clamped at the depth-appropriate left bound

    player.x = WIDTH - player.width
    player.update(_keys({pygame.K_RIGHT: True}), dt=16)
    assert player.x == WIDTH - margin - player.width


def test_player_falls_under_gravity_when_airborne():
    player = Player()
    player.on_ground = False
    player.y = 0
    player.update(NO_MOVE_KEYS, dt=16)
    assert player.vy == GRAVITY


def test_player_lands_and_resets_vertical_velocity():
    player = Player()
    player.on_ground = False
    player.y = player.ground_y - player.height + 5
    player.vy = 10
    player.update(NO_MOVE_KEYS, dt=16)
    assert player.on_ground is True
    assert player.vy == 0
    assert player.y == player.ground_y - player.height


def test_depth_movement_is_clamped_between_zero_and_one():
    player = Player()
    player.depth = 0.005
    for _ in range(10):
        player.update(_keys({pygame.K_UP: True}), dt=16)
    assert player.depth == 0.0

    player.depth = 0.995
    for _ in range(10):
        player.update(_keys({pygame.K_DOWN: True}), dt=16)
    assert player.depth == 1.0


def test_depth_movement_updates_ground_y_and_scale():
    player = Player()
    player.update(_keys({pygame.K_UP: True}), dt=16)
    assert player.depth == 0.55 - DEPTH_SPEED
    assert player.ground_y == ground_y_for_depth(player.depth)
    assert player.scale == scale_for_depth(player.depth)


def test_moving_toward_far_edge_narrows_x_bounds():
    player = Player()
    player.depth = 0.0  # far edge: widest margin, narrowest walkable area
    player.x = 0
    player.update(NO_MOVE_KEYS, dt=16)
    assert player.x == margin_for_depth(0.0)
    assert margin_for_depth(0.0) > margin_for_depth(1.0)


def test_landing_snaps_y_to_ground_when_depth_changes_while_grounded():
    player = Player()
    assert player.on_ground is True
    player.update(_keys({pygame.K_DOWN: True}), dt=16)
    assert player.y == player.ground_y - player.height


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
    player.jump()
    assert player.pending_bomb is True

    spawned_at_apex = False
    for _ in range(200):
        spawn_bomb = player.update(NO_MOVE_KEYS, dt=16)
        if spawn_bomb:
            spawned_at_apex = True
            break
        if player.on_ground:
            break

    assert spawned_at_apex
    assert player.pending_bomb is False


def test_create_bomb_inherits_players_depth_and_sits_on_its_ground():
    player = Player()
    player.depth = 0.2
    player.ground_y = ground_y_for_depth(0.2)

    bomb = player.create_bomb()

    assert bomb.depth == 0.2
    assert bomb.y == player.ground_y - 16


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
    player.x, player.y = 200, player.ground_y - player.height
    player.vx, player.vy = 0, 0
    player.on_ground = True

    origin_x = player.centerx - 50
    player.apply_explosion(origin_x=origin_x, origin_y=player.centery, radius=140)

    assert player.vx > 0  # pushed away from the origin, to the right
    assert player.vy < 0  # launched upward
    assert player.on_ground is False


def _player_dict(**overrides):
    data = {
        "x": 111, "y": 222, "vx": 3, "vy": -4, "on_ground": False,
        "bombs_left": 1, "pending_bomb": True, "bomb_cooldown": 250,
    }
    data.update(overrides)
    return data


def test_player_from_dict_builds_a_player_matching_the_dict():
    player = Player.from_dict(_player_dict())
    assert (player.x, player.y) == (111, 222)
    assert (player.vx, player.vy) == (3, -4)
    assert player.on_ground is False
    assert player.bombs_left == 1
    assert player.pending_bomb is True
    assert player.bomb_cooldown == 250
    assert player.rect.midbottom == (round(player.centerx), round(player.y + player.height))


def test_player_from_dict_defaults_missing_bomb_cooldown_to_zero():
    data = _player_dict()
    del data["bomb_cooldown"]
    player = Player.from_dict(data)
    assert player.bomb_cooldown == 0


def test_player_apply_dict_overwrites_an_existing_player_in_place():
    player = Player()
    player.apply_dict(_player_dict())
    assert (player.x, player.y) == (111, 222)
    assert player.rect.midbottom == (round(player.centerx), round(player.y + player.height))


def test_player_rect_matches_depth_scaled_size():
    player = Player()
    expected_w = max(1, int(player.width * player.scale))
    expected_h = max(1, int(player.height * player.scale))
    assert player.rect.size == (expected_w, expected_h)
    assert player.rect.midbottom == (round(player.centerx), round(player.y + player.height))


def test_player_rect_resizes_when_depth_changes():
    player = Player()
    player.update(_keys({pygame.K_UP: True}), dt=16)

    expected_w = max(1, int(player.width * player.scale))
    expected_h = max(1, int(player.height * player.scale))
    assert player.rect.size == (expected_w, expected_h)
    assert player.rect.midbottom == (round(player.centerx), round(player.y + player.height))
