import main


def test_bomb_not_ready_before_fuse_expires():
    bomb = main.Bomb(100, 100)
    bomb.update(dt=main.BOMB_FUSE_MS - 1)
    assert bomb.is_ready() is False


def test_bomb_ready_after_fuse_expires():
    bomb = main.Bomb(100, 100)
    bomb.update(dt=main.BOMB_FUSE_MS)
    assert bomb.is_ready() is True


def test_bomb_from_dict_round_trips_fields():
    original = main.Bomb(50, 60)
    original.timer = 321
    original.has_shrapnel = True
    restored = main.Bomb.from_dict(
        {"x": original.x, "y": original.y, "timer": original.timer, "has_shrapnel": original.has_shrapnel}
    )
    assert restored.x == original.x
    assert restored.y == original.y
    assert restored.timer == original.timer
    assert restored.has_shrapnel is True


def test_shard_is_alive_within_bounds_and_lifetime():
    shard = main.Shard(main.WIDTH / 2, main.HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is True


def test_shard_dies_when_lifetime_expires():
    shard = main.Shard(main.WIDTH / 2, main.HEIGHT / 2, angle=0, speed=0)
    shard.life = 0
    assert shard.is_alive() is False


def test_shard_dies_when_it_leaves_the_screen():
    shard = main.Shard(-10, main.HEIGHT / 2, angle=0, speed=0)
    assert shard.is_alive() is False


def test_enemy_takes_damage_and_dies_at_zero_hp():
    enemy = main.Enemy("left")
    enemy.hp = 2
    enemy.take_damage()
    assert enemy.hp == 1
    assert enemy.dead is False
    enemy.take_damage()
    assert enemy.hp == 0
    assert enemy.dead is True


def test_enemy_bounces_off_screen_edges():
    enemy = main.Enemy("left")
    enemy.x = 0
    enemy.vx = -3
    enemy.update(dt=16)
    assert enemy.x == 0
    assert enemy.vx == 3


def test_enemy_killed_by_explosion_within_range():
    enemy = main.Enemy("left")
    enemy.x, enemy.y = 100, main.GROUND_Y - enemy.height
    origin_x, origin_y = enemy.rect.centerx, enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is True


def test_enemy_not_killed_by_distant_explosion():
    enemy = main.Enemy("left")
    enemy.x, enemy.y = 100, main.GROUND_Y - enemy.height
    origin_x = enemy.rect.centerx + 1000
    origin_y = enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is False


def test_death_shrapnel_count_matches_enemy_type():
    enemy = main.Enemy("left")

    enemy.type = "grunt"
    assert len(enemy.get_death_shrapnel()) == 6

    enemy.type = "heavy"
    assert len(enemy.get_death_shrapnel()) == 5

    enemy.type = "elite"
    assert len(enemy.get_death_shrapnel()) == 8
