import pygame

from game.config import WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER, PLAYER_SPEED, GRAVITY
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
    assert player.jump_offset == 0


def test_player_spawns_within_world_bounds():
    player = Player()
    assert WORLD_BORDER <= player.x <= WORLD_WIDTH - WORLD_BORDER - player.width
    assert WORLD_BORDER <= player.y <= WORLD_HEIGHT - WORLD_BORDER - player.height


def test_player_shadow_anchor_is_its_feet_not_its_topleft():
    # Player stands upright (a rect entity, not circular) — its shadow
    # belongs at rect.midbottom (feet), matching the rendering contract
    # every drawable entity exposes (see rendering.draw_scene).
    player = Player()
    assert player.shadow_anchor == player.rect.midbottom


def test_player_move_left_right_clamped_to_the_stone_border():
    # The world's outer WORLD_BORDER pixels are a solid stone wall the
    # player can't walk into — clamp bounds are inset by that amount,
    # not the raw world edge.
    player = Player()

    player.x = WORLD_BORDER
    player.update(_keys({pygame.K_LEFT: True}), dt=16)
    assert player.x == WORLD_BORDER

    player.x = WORLD_WIDTH - WORLD_BORDER - player.width
    player.update(_keys({pygame.K_RIGHT: True}), dt=16)
    assert player.x == WORLD_WIDTH - WORLD_BORDER - player.width


def test_player_move_up_down_clamped_to_the_stone_border():
    player = Player()

    player.y = WORLD_BORDER
    player.update(_keys({pygame.K_UP: True}), dt=16)
    assert player.y == WORLD_BORDER

    player.y = WORLD_HEIGHT - WORLD_BORDER - player.height
    player.update(_keys({pygame.K_DOWN: True}), dt=16)
    assert player.y == WORLD_HEIGHT - WORLD_BORDER - player.height


def test_player_moves_up_and_down_by_player_speed():
    player = Player()
    start_y = player.y
    player.update(_keys({pygame.K_DOWN: True}), dt=16)
    assert player.y == start_y + PLAYER_SPEED

    player.update(_keys({pygame.K_UP: True}), dt=16)
    assert player.y == start_y


def test_player_falls_under_gravity_when_airborne():
    player = Player()
    player.on_ground = False
    player.vy = -5
    player.update(NO_MOVE_KEYS, dt=16)
    assert player.vy == -5 + GRAVITY


def test_player_lands_and_resets_jump_offset():
    player = Player()
    player.on_ground = False
    player.jump_offset = -5
    player.vy = 10
    player.update(NO_MOVE_KEYS, dt=16)
    assert player.on_ground is True
    assert player.vy == 0
    assert player.jump_offset == 0


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


def test_jump_does_not_move_world_position():
    player = Player()
    start_x, start_y = player.x, player.y
    player.jump()
    player.update(NO_MOVE_KEYS, dt=16)
    assert (player.x, player.y) == (start_x, start_y)


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


def test_create_bomb_spawns_at_players_feet():
    player = Player()
    player.x, player.y = 300, 400

    bomb = player.create_bomb()

    assert bomb.x == player.centerx
    assert bomb.y == player.y + player.height


def test_create_bomb_passes_players_jump_offset_as_fall_offset():
    player = Player()
    player.jump_offset = -63

    bomb = player.create_bomb()

    assert bomb.fall_offset == -63


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
    player.x, player.y = 200, 400
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


def test_player_rect_matches_fixed_size():
    player = Player()
    assert player.rect.size == (player.width, player.height)
    assert player.rect.midbottom == (round(player.centerx), round(player.y + player.height))


def test_player_rect_tracks_world_position_after_move():
    player = Player()
    player.update(_keys({pygame.K_DOWN: True}), dt=16)

    assert player.rect.size == (player.width, player.height)
    assert player.rect.midbottom == (round(player.centerx), round(player.y + player.height))


def test_player_to_dict_round_trips_through_from_dict():
    original = Player()
    original.x, original.y = 111, 222
    original.vx, original.vy = 3, -4
    original.on_ground = False
    original.bombs_left = 1
    original.pending_bomb = True
    original.bomb_cooldown = 250

    restored = Player.from_dict(original.to_dict())

    assert (restored.x, restored.y) == (original.x, original.y)
    assert (restored.vx, restored.vy) == (original.vx, original.vy)
    assert restored.on_ground == original.on_ground
    assert restored.bombs_left == original.bombs_left
    assert restored.pending_bomb == original.pending_bomb
    assert restored.bomb_cooldown == original.bomb_cooldown
