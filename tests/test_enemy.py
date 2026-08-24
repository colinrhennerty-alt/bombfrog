from game.simulation.depth import margin_for_depth, scale_for_depth
from game.simulation.enemy import Enemy


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


def test_enemy_rect_matches_depth_scaled_size():
    enemy = Enemy("left")
    scale = scale_for_depth(enemy.depth)
    expected_w = max(1, int(enemy.width * scale))
    expected_h = max(1, int(enemy.height * scale))
    assert enemy.rect.size == (expected_w, expected_h)
    assert enemy.rect.midbottom == (round(enemy.x + enemy.width / 2), round(enemy.y + enemy.height))


def test_enemy_rect_resizes_after_update():
    enemy = Enemy("left")
    enemy.depth = 0.0  # force a different scale than spawn
    enemy.update(dt=16)
    scale = scale_for_depth(0.0)
    expected_w = max(1, int(enemy.width * scale))
    expected_h = max(1, int(enemy.height * scale))
    assert enemy.rect.size == (expected_w, expected_h)


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
