from game.config import WIDTH, HEIGHT, BOMB_FUSE_MS
from game.depth import margin_for_depth, scale_for_depth
from game.entities import Player, Bomb, Shard, Enemy


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
    assert player.rect.topleft == (111, 222)


def test_player_from_dict_defaults_missing_bomb_cooldown_to_zero():
    data = _player_dict()
    del data["bomb_cooldown"]
    player = Player.from_dict(data)
    assert player.bomb_cooldown == 0


def test_player_apply_dict_overwrites_an_existing_player_in_place():
    player = Player()
    player.apply_dict(_player_dict())
    assert (player.x, player.y) == (111, 222)
    assert player.rect.topleft == (111, 222)


def test_bomb_not_ready_before_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_FUSE_MS - 1)
    assert bomb.is_ready() is False


def test_bomb_ready_after_fuse_expires():
    bomb = Bomb(100, 100)
    bomb.update(dt=BOMB_FUSE_MS)
    assert bomb.is_ready() is True


def test_bomb_from_dict_round_trips_fields():
    original = Bomb(50, 60, depth=0.3)
    original.timer = 321
    original.has_shrapnel = True
    restored = Bomb.from_dict(
        {
            "x": original.x, "y": original.y, "timer": original.timer,
            "has_shrapnel": original.has_shrapnel, "depth": original.depth,
        }
    )
    assert restored.x == original.x
    assert restored.y == original.y
    assert restored.timer == original.timer
    assert restored.has_shrapnel is True
    assert restored.depth == 0.3


def test_bomb_defaults_to_near_depth_and_full_scale():
    bomb = Bomb(50, 60)
    assert bomb.depth == 1.0
    assert bomb.scale == scale_for_depth(1.0)


def test_bomb_from_dict_defaults_missing_depth_to_one():
    data = {"x": 1, "y": 2, "timer": 100}
    bomb = Bomb.from_dict(data)
    assert bomb.depth == 1.0


def test_shard_is_alive_within_bounds_and_lifetime():
    shard = Shard(WIDTH / 2, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is True


def test_shard_dies_when_lifetime_expires():
    shard = Shard(WIDTH / 2, HEIGHT / 2, angle=0, speed=0)
    shard.life = 0
    assert shard.is_alive() is False


def test_shard_dies_when_it_leaves_the_screen():
    shard = Shard(-10, HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is False


def test_enemy_takes_damage_and_dies_at_zero_hp():
    enemy = Enemy("left")
    enemy.hp = 2
    enemy.take_damage()
    assert enemy.hp == 1
    assert enemy.dead is False
    enemy.take_damage()
    assert enemy.hp == 0
    assert enemy.dead is True


def test_enemy_bounces_off_screen_edges_at_its_own_depth_margin():
    enemy = Enemy("left")
    enemy.depth = 0.5
    margin = margin_for_depth(0.5)
    enemy.x = margin
    enemy.vx = -3
    enemy.update(dt=16)
    assert enemy.x == margin
    assert enemy.vx == 3


def test_enemy_spawns_with_depth_in_expected_range():
    for _ in range(20):
        enemy = Enemy("left")
        assert 0.1 <= enemy.depth <= 0.95


def test_enemy_killed_by_explosion_within_range():
    enemy = Enemy("left")
    enemy.x = 100
    origin_x, origin_y = enemy.rect.centerx, enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is True


def test_enemy_not_killed_by_distant_explosion():
    enemy = Enemy("left")
    enemy.x = 100
    origin_x = enemy.rect.centerx + 1000
    origin_y = enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is False


def test_enemy_from_dict_round_trips_depth():
    enemy = Enemy("left")
    restored = Enemy.from_dict(
        {
            "x": enemy.x, "y": enemy.y, "vx": enemy.vx, "type": enemy.type,
            "dead": enemy.dead, "depth": 0.42,
        }
    )
    assert restored.depth == 0.42


def test_death_shrapnel_count_matches_enemy_type():
    enemy = Enemy("left")

    enemy.type = "grunt"
    assert len(enemy.get_death_shrapnel()) == 6

    enemy.type = "heavy"
    assert len(enemy.get_death_shrapnel()) == 5

    enemy.type = "elite"
    assert len(enemy.get_death_shrapnel()) == 8
