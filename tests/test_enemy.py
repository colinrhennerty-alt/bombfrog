from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WORLD_BORDER
from game.simulation.camera import Camera
from game.simulation.enemy import Enemy


def test_enemy_takes_damage_and_dies_at_zero_hp():
    enemy = Enemy("left", 500, 500)
    enemy.hp = 2
    enemy.take_damage()
    assert enemy.hp == 1
    assert enemy.dead is False
    enemy.take_damage()
    assert enemy.hp == 0
    assert enemy.dead is True


def test_enemy_bounces_off_the_stone_border():
    # Same inset boundary as the player — enemies bounce off the border
    # zone, not the raw world edge, so they never visually clip into it.
    enemy = Enemy("left", 500, 500)
    enemy.x = WORLD_BORDER
    enemy.vx = -3
    enemy.update(dt=16)
    assert enemy.x == WORLD_BORDER
    assert enemy.vx == 3


def test_enemy_bounces_off_the_far_stone_border():
    enemy = Enemy("left", 500, 500)
    enemy.x = WORLD_WIDTH - WORLD_BORDER - enemy.width
    enemy.vx = 3
    enemy.update(dt=16)
    assert enemy.x == WORLD_WIDTH - WORLD_BORDER - enemy.width
    assert enemy.vx == -3


def test_enemy_spawns_clamped_within_the_stone_border():
    for _ in range(20):
        enemy = Enemy("left", 500, 500)
        assert WORLD_BORDER <= enemy.x <= WORLD_WIDTH - WORLD_BORDER - enemy.width
        assert WORLD_BORDER <= enemy.y <= WORLD_HEIGHT - WORLD_BORDER - enemy.height


def test_enemy_spawns_off_screen_near_left_world_edge():
    # Player near the left world edge: the camera clamps to x=0, so the
    # visible viewport is [0, WIDTH]. A "left" spawn must land outside
    # that viewport, not get clamped back onto the visible screen.
    player_x, player_y = 50, 500
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.snap_to(player_x, player_y)

    enemy = Enemy("left", player_x, player_y, camera=camera)

    assert enemy.x + enemy.width <= camera.x or enemy.x >= camera.x + camera.viewport_width


def test_enemy_spawns_off_screen_near_right_world_edge():
    player_x, player_y = WORLD_WIDTH - 50, 500
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.snap_to(player_x, player_y)

    enemy = Enemy("right", player_x, player_y, camera=camera)

    assert enemy.x + enemy.width <= camera.x or enemy.x >= camera.x + camera.viewport_width


def test_enemy_rect_matches_fixed_size():
    enemy = Enemy("left", 500, 500)
    assert enemy.rect.size == (enemy.width, enemy.height)
    assert enemy.rect.midbottom == (round(enemy.x + enemy.width / 2), round(enemy.y + enemy.height))


def test_enemy_rect_moves_after_update():
    enemy = Enemy("left", 500, 500)
    enemy.vx = 3
    enemy.update(dt=16)
    assert enemy.rect.midbottom == (round(enemy.x + enemy.width / 2), round(enemy.y + enemy.height))


def test_enemy_killed_by_explosion_within_range():
    enemy = Enemy("left", 500, 500)
    enemy.x = 100
    origin_x, origin_y = enemy.rect.centerx, enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is True


def test_enemy_not_killed_by_distant_explosion():
    enemy = Enemy("left", 500, 500)
    enemy.x = 100
    origin_x = enemy.rect.centerx + 1000
    origin_y = enemy.rect.centery
    assert enemy.killed_by_explosion(origin_x, origin_y, radius=100) is False


def test_enemy_from_dict_round_trips_position():
    enemy = Enemy("left", 500, 500)
    restored = Enemy.from_dict(
        {
            "x": enemy.x, "y": enemy.y, "vx": enemy.vx, "type": enemy.type,
            "dead": enemy.dead,
        }
    )
    assert restored.x == enemy.x
    assert restored.y == enemy.y


def test_death_shrapnel_count_matches_enemy_type():
    enemy = Enemy("left", 500, 500)

    enemy.type = "grunt"
    assert len(enemy.get_death_shrapnel()) == 6

    enemy.type = "heavy"
    assert len(enemy.get_death_shrapnel()) == 5

    enemy.type = "elite"
    assert len(enemy.get_death_shrapnel()) == 8


class _FakeRng:
    """Duck-typed stand-in for the `random` module: returns fixed,
    caller-chosen values for the exact calls Enemy makes instead of an
    actual random draw, and records how each was called."""

    def __init__(self, choice_result, uniform_result):
        self.choice_result = choice_result
        self.uniform_result = uniform_result
        self.choices_calls = []
        self.uniform_calls = []

    def choices(self, population, weights):
        self.choices_calls.append((population, weights))
        return [self.choice_result]

    def uniform(self, low, high):
        self.uniform_calls.append((low, high))
        return self.uniform_result


def test_enemy_uses_injected_rng_to_pick_type_and_spawn_offset():
    fake = _FakeRng(choice_result="elite", uniform_result=0)
    enemy = Enemy("left", 500, 500, rng=fake)

    assert enemy.type == "elite"
    assert len(fake.choices_calls) == 1
    assert len(fake.uniform_calls) == 1


def test_enemy_injected_rng_controls_spawn_y_offset_deterministically():
    fake = _FakeRng(choice_result="grunt", uniform_result=37)
    enemy = Enemy("left", 500, 500, rng=fake)

    assert enemy.y == 500 + 37


def test_enemy_shadow_anchor_is_its_feet_not_its_topleft():
    # Enemy stands upright (a rect entity, not circular) — its shadow
    # belongs at rect.midbottom (feet), matching the rendering contract
    # every drawable entity exposes (see rendering.draw_scene).
    enemy = Enemy("left", 500, 500)
    assert enemy.shadow_anchor == enemy.rect.midbottom
