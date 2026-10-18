"""Smoke tests: every draw_* function runs against a real surface without
raising. Rendering correctness itself stays a manual/visual check.
"""

import pygame
import pytest

from game.config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, ENTITY_SCALE
from game.simulation.camera import Camera
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy
from game.simulation.explosion_effect import ExplosionEffect
from game.rendering import entities, tile_geometry, ground, editor_view, hud
from game.rendering.assets import get_frog_frames


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
    entities.draw_shadow(surface, 100, 100, base_radius=20)


def test_draw_shadow_shrinks_with_height_offset(surface):
    # height_offset represents how far above the ground the entity is
    # (same magnitude convention as jump_offset/fall_offset — 0 is grounded).
    # The shadow should shrink and fade as height increases, since that's
    # the depth cue that sells verticality.
    grounded = entities.shadow_size_for(base_radius=20, height_offset=0)
    airborne = entities.shadow_size_for(base_radius=20, height_offset=80)
    assert airborne < grounded


def test_draw_shadow_accepts_height_offset(surface):
    entities.draw_shadow(surface, 100, 100, base_radius=20, height_offset=80)


def test_grounded_shadow_width_stays_within_the_entitys_own_footprint():
    # base_radius is passed as the entity's full width for rect-based
    # entities (Player/Enemy) — the shadow's full width (shadow_size_for
    # returns a radius, so double it) must not exceed that, or it visibly
    # overhangs the sprite's own silhouette instead of sitting under it.
    base_radius = 52  # e.g. Player.width
    shadow_radius = entities.shadow_size_for(base_radius, height_offset=0)
    assert shadow_radius * 2 <= base_radius


def test_draw_player(surface, camera):
    entities.draw_player(surface, Player(), camera)


def test_draw_player_jump_pose(surface, camera):
    player = Player()
    player.on_ground = False
    entities.draw_player(surface, player, camera)


def test_draw_player_landing_pose(surface, camera):
    player = Player()
    player.land_timer = 60
    entities.draw_player(surface, player, camera)


def test_draw_player_idle_animation_frame_and_facing_flip(surface, camera):
    player = Player()
    player.anim_index = 3
    player.facing = -1
    entities.draw_player(surface, player, camera)
    player.facing = 1
    entities.draw_player(surface, player, camera)


class _BlitRecordingSurface:
    """Duck-typed stand-in for pygame.Surface: real Surface.blit can't be
    monkeypatched (it's a C extension type), so this just records what it
    was asked to blit instead of a real target."""

    def __init__(self):
        self.captured = None

    def blit(self, source, dest):
        dest_rect = pygame.Rect(dest, source.get_size()) if not isinstance(dest, pygame.Rect) else dest
        self.captured = (source.get_size(), dest_rect.topleft)
        self.source = source


def test_draw_player_blits_the_frog_unstretched_with_its_feet_on_the_hitbox_bottom(camera):
    # The frog frame is drawn at one uniform pixel scale (no stretching),
    # as wide as the hitbox, with its bottom-center on the hitbox's
    # midbottom — the hitbox is the grounded body; the jump pose's extra
    # height just extends upward past it.
    player = Player()
    fake_surface = _BlitRecordingSurface()

    entities.draw_player(fake_surface, player, camera)

    (width, height), topleft = fake_surface.captured
    native_w, native_h = get_frog_frames()["idle"][0].get_size()
    assert width == player.rect.size[0]
    assert height == round(native_h * width / native_w)
    screen_rect = camera.apply_rect(player.rect)
    assert (topleft[0] + width // 2, topleft[1] + height) == screen_rect.midbottom


def test_draw_player_moves_up_the_screen_while_airborne(camera):
    # jump_offset accumulates negative while rising (Player._apply_jump_physics
    # adds a negative vy each tick) — the drawn sprite must move to a smaller
    # screen y (up), not a larger one (down), as it climbs.
    player = Player()
    player.on_ground = False
    player.jump_offset = -50
    fake_surface = _BlitRecordingSurface()

    entities.draw_player(fake_surface, player, camera)

    _, airborne_topleft = fake_surface.captured
    player.on_ground = True
    player.jump_offset = 0
    entities.draw_player(fake_surface, player, camera)
    _, grounded_topleft = fake_surface.captured
    assert airborne_topleft[1] == grounded_topleft[1] - 50


def test_draw_enemy_blits_sprite_sized_and_positioned_to_match_the_collision_rect(camera):
    enemy = Enemy("left", 500, 500)
    fake_surface = _BlitRecordingSurface()

    entities.draw_enemy(fake_surface, enemy, camera)

    size, topleft = fake_surface.captured
    assert size == enemy.rect.size
    assert topleft == camera.apply_rect(enemy.rect).topleft


def _solid_frame(color):
    frame = pygame.Surface((8, 8))
    frame.fill(color)
    return frame


@pytest.fixture
def colored_critter_frames(monkeypatch):
    """Stubs every critter with solid-color frames so a test can tell
    which facing/frame was drawn from the blitted surface's color alone:
    red channel = facing (SE 100, SW 200), green channel = frame index."""
    frames = {
        critter: {
            facing: [_solid_frame((red, i, 0)) for i in range(3)]
            for facing, red in (("SE", 100), ("SW", 200))
        }
        for critter in ("badger", "boar", "stag")
    }
    monkeypatch.setattr(entities, "get_critter_frames", lambda: frames)
    return frames


def _drawn_color(enemy, camera):
    fake_surface = _BlitRecordingSurface()
    entities.draw_enemy(fake_surface, enemy, camera)
    return tuple(fake_surface.source.get_at((0, 0)))[:3]


def test_draw_enemy_uses_se_frames_moving_right_and_sw_frames_moving_left(camera, colored_critter_frames):
    enemy = Enemy("left", 500, 500)
    enemy.type = "grunt"
    enemy.vx = 2.2
    assert _drawn_color(enemy, camera)[0] == 100
    enemy.vx = -2.2
    assert _drawn_color(enemy, camera)[0] == 200


def test_draw_enemy_cycles_frames_with_anim_index(camera, colored_critter_frames):
    enemy = Enemy("left", 500, 500)
    enemy.type = "grunt"
    enemy.vx = 2.2
    frame_count = len(colored_critter_frames["badger"]["SE"])
    enemy.anim_index = 1
    assert _drawn_color(enemy, camera)[1] == 1
    enemy.anim_index = frame_count + 1
    assert _drawn_color(enemy, camera)[1] == 1


def test_depth_scale_is_smaller_near_the_top_than_the_bottom_of_the_viewport():
    # Mimics a camera looking down at an angle rather than straight down:
    # entities drawn near the top of the screen (further away) read smaller
    # than ones near the bottom (closer), independent of their world size.
    near_top = entities.depth_scale_for(0)
    near_bottom = entities.depth_scale_for(HEIGHT)
    assert near_top < near_bottom


def test_draw_bomb_is_smaller_near_the_top_of_the_viewport(surface, camera, monkeypatch):
    captured_radii = []
    original_circle = pygame.draw.circle

    def fake_circle(surface_, color, center, radius, *args, **kwargs):
        captured_radii.append(radius)
        return original_circle(surface_, color, center, radius, *args, **kwargs)

    monkeypatch.setattr(pygame.draw, "circle", fake_circle)
    entities.draw_bomb(surface, Bomb(100, 0), camera)
    top_radius = captured_radii[0]

    captured_radii.clear()
    entities.draw_bomb(surface, Bomb(100, HEIGHT), camera)
    bottom_radius = captured_radii[0]

    assert top_radius < bottom_radius


def test_draw_bomb(surface, camera):
    entities.draw_bomb(surface, Bomb(100, 100), camera)


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
    entities.draw_bomb(surface, bomb, camera)

    ground_x, ground_y = camera.apply(bomb.x, bomb.y)
    drawn_x, drawn_y = captured["centers"][0]
    assert drawn_x == int(ground_x)
    assert drawn_y < ground_y


def test_draw_bomb_explosion_radius(surface, camera):
    entities.draw_bomb_explosion_radius(surface, Bomb(100, 100), camera)


def test_draw_shard(surface, camera):
    entities.draw_shard(surface, Shard(100, 100, angle=0, speed=5), camera)


def test_draw_shard_is_smaller_near_the_top_of_the_viewport(surface, camera, monkeypatch):
    captured_radii = []
    original_circle = pygame.draw.circle

    def fake_circle(surface_, color, center, radius, *args, **kwargs):
        captured_radii.append(radius)
        return original_circle(surface_, color, center, radius, *args, **kwargs)

    monkeypatch.setattr(pygame.draw, "circle", fake_circle)
    entities.draw_shard(surface, Shard(100, 0, angle=0, speed=5), camera)
    top_radius = captured_radii[0]

    captured_radii.clear()
    entities.draw_shard(surface, Shard(100, HEIGHT, angle=0, speed=5), camera)
    bottom_radius = captured_radii[0]

    assert top_radius < bottom_radius


def test_draw_enemy_each_type(surface, camera):
    for enemy_type in ("grunt", "heavy", "elite"):
        enemy = Enemy("left", 500, 500)
        enemy.type = enemy_type
        entities.draw_enemy(surface, enemy, camera)


def test_draw_explosion_effect(surface, camera):
    entities.draw_explosion_effect(surface, ExplosionEffect(100, 100, radius=140), camera)


def test_draw_scene_shrinks_airborne_players_shadow(surface, camera, monkeypatch):
    # draw_scene must read the player's jump_offset and the bomb's
    # fall_offset and pass them into draw_shadow, not always draw a
    # grounded-size shadow.
    player = Player()
    player.jump_offset = -90
    bomb = Bomb(300, 300, fall_offset=-90)

    captured_offsets = []
    original_shadow = entities.draw_shadow

    def fake_shadow(surface_, x, y, base_radius, height_offset=0):
        captured_offsets.append(height_offset)
        return original_shadow(surface_, x, y, base_radius, height_offset)

    monkeypatch.setattr(entities, "draw_shadow", fake_shadow)
    entities.draw_scene(surface, player=player, bombs=[bomb], shards=[], enemies=[], effects=[], camera=camera)

    assert -90 in captured_offsets


def test_draw_scene_draws_the_players_shadow_at_its_feet_not_its_topleft(monkeypatch):
    # Regression: player.x/y is the rect's top-left corner, not its
    # center (Bomb/Shard use x/y as their true center, but Player and
    # Enemy don't) — drawing the shadow at camera.apply(entity.x, entity.y)
    # placed it offset up-and-left of the sprite instead of directly
    # beneath it. Anchored to rect.midbottom (feet), not rect.center, so
    # it reads as cast on the ground under the sprite rather than sitting
    # near its torso/behind it.
    player = Player()
    player.x, player.y = 500, 500  # comfortably inside the viewport
    player._sync_rect()

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.snap_to(player.centerx, player.centery)

    captured_positions = []
    original_shadow = entities.draw_shadow

    def fake_shadow(surface_, x, y, base_radius, height_offset=0):
        captured_positions.append((x, y))
        return original_shadow(surface_, x, y, base_radius, height_offset)

    monkeypatch.setattr(entities, "draw_shadow", fake_shadow)
    fake_surface = pygame.Surface((WIDTH, HEIGHT))
    entities.draw_scene(fake_surface, player=player, bombs=[], shards=[], enemies=[], effects=[], camera=camera)

    expected = camera.apply(*player.rect.midbottom)
    assert captured_positions[0] == expected


def test_draw_scene_skips_the_generated_shadow_for_enemies_whose_art_has_one(monkeypatch):
    # The critter sprites carry a shadow baked into the art; drawing the
    # generated ellipse at rect.midbottom too left a second shadow under
    # the baked one, which read as the enemy hovering off the ground.
    player = Player()
    player.x, player.y = 500, 500
    player._sync_rect()
    enemy = Enemy("left", 500, 500)

    shadow_calls = []
    monkeypatch.setattr(entities, "draw_shadow", lambda *args, **kwargs: shadow_calls.append(args))
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    entities.draw_scene(
        pygame.Surface((WIDTH, HEIGHT)), player=player, bombs=[], shards=[], enemies=[enemy], effects=[], camera=camera
    )

    assert len(shadow_calls) == 1  # the player's only


def test_draw_scene_draws_a_bombs_shadow_at_its_center(monkeypatch):
    # Bomb/Shard are circular with no "feet" — their rect.center is
    # already the correct shadow anchor, unlike rect-based entities.
    bomb = Bomb(500, 500)

    captured_positions = []
    original_shadow = entities.draw_shadow

    def fake_shadow(surface_, x, y, base_radius, height_offset=0):
        captured_positions.append((x, y))
        return original_shadow(surface_, x, y, base_radius, height_offset)

    monkeypatch.setattr(entities, "draw_shadow", fake_shadow)
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    fake_surface = pygame.Surface((WIDTH, HEIGHT))
    entities.draw_scene(fake_surface, player=None, bombs=[bomb], shards=[], enemies=[], effects=[], camera=camera)

    expected = camera.apply(*bomb.rect.center)
    assert captured_positions[0] == expected


def test_draw_scene_with_full_cast(surface, camera):
    entities.draw_scene(
        surface,
        player=Player(),
        bombs=[Bomb(100, 100)],
        shards=[Shard(100, 100, angle=0, speed=5)],
        enemies=[Enemy("left", 500, 500)],
        effects=[ExplosionEffect(100, 100, radius=140)],
        camera=camera,
    )


def test_draw_scene_with_no_player(surface, camera):
    entities.draw_scene(surface, player=None, bombs=[], shards=[], enemies=[], effects=[], camera=camera)


def test_draw_debug_boxes_with_full_cast(surface, camera):
    entities.draw_debug_boxes(
        surface,
        player=Player(),
        bombs=[Bomb(100, 100)],
        shards=[Shard(100, 100, angle=0, speed=5)],
        enemies=[Enemy("left", 500, 500)],
        camera=camera,
    )


def test_draw_debug_boxes_with_no_player(surface, camera):
    entities.draw_debug_boxes(surface, player=None, bombs=[], shards=[], enemies=[], camera=camera)


def test_draw_debug_boxes_draws_each_entitys_actual_collision_rect(surface):
    surface.fill((0, 0, 0))
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    player = Player()
    player.x, player.y = 100, 100  # comfortably inside the viewport regardless of camera clamp
    player._sync_rect()
    camera.snap_to(player.centerx, player.centery)
    entities.draw_debug_boxes(surface, player=player, bombs=[], shards=[], enemies=[], camera=camera)
    # the outline is drawn exactly on the camera-translated rect: sample its border pixel
    screen_rect = camera.apply_rect(player.rect)
    color_at_top_left = surface.get_at(screen_rect.topleft)[:3]
    assert color_at_top_left != (0, 0, 0)


class _MultiBlitRecordingSurface:
    """Like _BlitRecordingSurface, but keeps every blit call — draw_ground
    blits many tiles in one call, not just one sprite."""

    def __init__(self):
        self.calls = []

    def blit(self, source, dest):
        dest_rect = pygame.Rect(dest, source.get_size()) if not isinstance(dest, pygame.Rect) else dest
        self.calls.append((source.get_size(), dest_rect.topleft))

    def fill(self, color):
        pass


def test_draw_ground(surface, camera):
    ground.draw_ground(surface, camera)


def test_draw_editor_with_empty_tilemap(surface):
    from game.scene.editor_state import EditorState

    editor_state = EditorState(WIDTH, HEIGHT)
    editor_view.draw_editor(surface, editor_state)


def test_draw_editor_with_painted_tiles_and_hover(surface):
    from game.scene.editor_state import EditorState

    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.camera.x, editor_state.camera.y = 0, 0
    editor_state.tilemap.set_tile(2, 2, editor_state.palette[0])
    editor_state.hover_col, editor_state.hover_row = 3, 3

    editor_view.draw_editor(surface, editor_state)


def test_draw_editor_with_a_wall_cell(surface):
    from game.scene.editor_state import EditorState

    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.camera.x, editor_state.camera.y = 0, 0
    editor_state.tilemap.set_tile(2, 2, editor_state.palette[0], is_wall=True)

    editor_view.draw_editor(surface, editor_state)


def test_draw_editor_sidebar_without_a_font(surface):
    from game.scene.editor_state import EditorState

    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.select_tile(1)

    editor_view.draw_editor_sidebar(surface, editor_state)


def test_draw_editor_sidebar_with_a_font_renders_button_labels(surface, fonts):
    from game.scene.editor_state import EditorState

    _, small_font = fonts
    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.select_tile(1)

    editor_view.draw_editor_sidebar(surface, editor_state, small_font)


def test_draw_editor_sidebar_with_wall_mode_on(surface, fonts):
    from game.scene.editor_state import EditorState

    _, small_font = fonts
    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.wall_mode = True

    editor_view.draw_editor_sidebar(surface, editor_state, small_font)


def test_draw_editor_sidebar_with_reset_pending(surface, fonts):
    from game.scene.editor_state import EditorState

    _, small_font = fonts
    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.reset_pending = True

    editor_view.draw_editor_sidebar(surface, editor_state, small_font)


def test_draw_editor_does_not_draw_ground_tiles_into_the_sidebar_region(surface):
    from game.scene.editor_state import EditorState

    editor_state = EditorState(WIDTH, HEIGHT)
    editor_state.camera.x, editor_state.camera.y = 0, 0
    # Every ground tile the map draws must stay left of its own (shrunk)
    # viewport — the sidebar area is reserved for draw_editor_sidebar.
    editor_view.draw_editor(surface, editor_state)


def test_visible_tile_range_does_not_extend_below_zero_at_the_worlds_origin():
    # The camera sits at the world's top-left corner (0, 0) — the tile
    # range must not include negative columns/rows, since there's no
    # ground there for the player to ever reach.
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = 0, 0

    min_col, max_col, min_row, max_row = tile_geometry.visible_tile_range(camera)

    assert min_col >= 0
    assert min_row >= 0


def test_visible_tile_range_does_not_exceed_the_worlds_far_edge():
    # The camera sits at the world's bottom-right corner — the tile range
    # must not extend past WORLD_WIDTH/WORLD_HEIGHT (in tile units). Row
    # units are TILE_FOOTPRINT_HEIGHT/2 (matching the scroll rate fix, see
    # test_ground_scrolls_at_the_same_rate_as_every_other_entity), not
    # TILE_WIDTH — cols and rows use different pixel-per-unit scales.
    from game.rendering.tile_geometry import TILE_WIDTH, TILE_FOOTPRINT_HEIGHT

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = WORLD_WIDTH, WORLD_HEIGHT

    min_col, max_col, min_row, max_row = tile_geometry.visible_tile_range(camera)

    assert max_col <= WORLD_WIDTH / TILE_WIDTH
    assert max_row <= WORLD_HEIGHT / (TILE_FOOTPRINT_HEIGHT / 2)


def test_draw_ground_scrolls_straight_when_camera_moves_purely_vertically():
    # Regression for the reported bug: moving straight up/down felt
    # rotated 45 degrees on the tiled ground. A pure-vertical camera move
    # must shift every tile's screen position only in y, never in x.
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = WORLD_WIDTH / 2, WORLD_HEIGHT / 2

    before = _MultiBlitRecordingSurface()
    ground.draw_ground(before, camera)

    camera.y -= 100  # pure vertical move, x unchanged

    after = _MultiBlitRecordingSurface()
    ground.draw_ground(after, camera)

    before_xs = sorted({topleft[0] for _, topleft in before.calls})
    after_xs = sorted({topleft[0] for _, topleft in after.calls})
    assert before_xs == after_xs


def test_ground_scrolls_at_the_same_rate_as_every_other_entity():
    # Regression: bombs/enemies/player all move via Camera.apply, a 1:1
    # world-unit-to-screen-pixel mapping. The ground must scroll at that
    # same rate, or entities visually drift off the tiles they're
    # standing on as the camera moves (reported bug: "bombs and enemies
    # are still moving relative to the old flat game and not the new
    # tiles"). Track the same physical world tile's screen position
    # (fixed world_row, camera-relative row recomputed each time) across
    # a vertical camera move and confirm it shifts by exactly the delta,
    # matching what camera.apply produces for any entity.
    from game.rendering.tile_geometry import TILE_WIDTH, TILE_FOOTPRINT_HEIGHT

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = WORLD_WIDTH / 2, WORLD_HEIGHT / 2
    half_h = TILE_FOOTPRINT_HEIGHT / 2
    fixed_world_row = int(camera.y / half_h)  # a tile at the camera's own row

    def screen_y_of_fixed_tile():
        cam_row = camera.y / half_h
        _, sy = tile_geometry.ground_tile_screen_pos(
            0, fixed_world_row - cam_row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=fixed_world_row
        )
        return sy

    fixed_world_point_y = WORLD_HEIGHT / 2
    before_tile_y = screen_y_of_fixed_tile()
    before_entity_y = camera.apply(0, fixed_world_point_y)[1]

    camera.y += 96  # arbitrary pure-vertical move

    after_tile_y = screen_y_of_fixed_tile()
    after_entity_y = camera.apply(0, fixed_world_point_y)[1]

    tile_shift = before_tile_y - after_tile_y
    entity_shift = before_entity_y - after_entity_y
    assert entity_shift == 96  # sanity: camera.apply is 1:1, as documented
    assert tile_shift == entity_shift


def test_draw_ground_tiles_the_grass_tile_across_the_viewport(camera):
    from game.rendering.tile_geometry import TILE_WIDTH, TILE_HEIGHT

    fake_surface = _MultiBlitRecordingSurface()
    ground.draw_ground(fake_surface, camera)

    assert len(fake_surface.calls) > 1
    assert all(size == (TILE_WIDTH, TILE_HEIGHT) for size, _ in fake_surface.calls)


def test_draw_ground_covers_the_full_viewport_away_from_world_edges():
    # Every screen pixel should fall under some tile when the camera is
    # comfortably inside the world — no gaps from an under-sized iso grid.
    # (Near a world edge the ground is expected to stop short of the
    # viewport, since there's no ground beyond WORLD_WIDTH/WORLD_HEIGHT —
    # see test_draw_ground_does_not_tile_past_the_worlds_edges.)
    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = WORLD_WIDTH / 2, WORLD_HEIGHT / 2

    fake_surface = _MultiBlitRecordingSurface()
    ground.draw_ground(fake_surface, camera)

    covered = pygame.Rect(0, 0, 0, 0)
    for size, topleft in fake_surface.calls:
        covered = covered.union(pygame.Rect(topleft, size))

    viewport = pygame.Rect(0, 0, WIDTH, HEIGHT)
    assert covered.contains(viewport)


def test_draw_ground_covers_the_full_viewport_across_a_sweep_of_camera_positions():
    # Regression: a single fixed camera position isn't enough to catch a
    # padding bug in visible_tile_range — only ~55% of arbitrary camera
    # positions actually failed before this was fixed, since the gap only
    # appears depending on cam_col/cam_row's fractional part and whether
    # the visible row range happens to include an odd (staggered) row.
    # This read as "the screen flickers a lot while moving": the ground
    # would intermittently fail to cover the viewport, flashing the navy
    # background through the gap.
    viewport = pygame.Rect(0, 0, WIDTH, HEIGHT)
    # Comfortably inside the world on every axis, including the viewport's
    # own extent (camera.x/y is the viewport's top-left corner, not its
    # center) — so world-edge clipping (a separate, correct behavior)
    # never explains a gap here.
    margin = 300
    for cx in range(margin, WORLD_WIDTH - WIDTH - margin, 37):
        for cy in range(margin, WORLD_HEIGHT - HEIGHT - margin, 41):
            camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
            camera.x, camera.y = cx, cy
            fake_surface = _MultiBlitRecordingSurface()
            ground.draw_ground(fake_surface, camera)

            covered = pygame.Rect(0, 0, 0, 0)
            for size, topleft in fake_surface.calls:
                covered = covered.union(pygame.Rect(topleft, size))

            assert covered.contains(viewport), f"gap at camera=({cx}, {cy})"


def test_draw_ground_does_not_tile_past_the_worlds_edges():
    # At the world's origin corner, no tile should be blitted representing
    # ground above/left of world (0, 0) — there's nothing there for the
    # player to ever reach.
    from game.rendering.tile_geometry import TILE_WIDTH

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = 0, 0

    fake_surface = _MultiBlitRecordingSurface()
    ground.draw_ground(fake_surface, camera)

    min_col, max_col, min_row, max_row = tile_geometry.visible_tile_range(camera)
    assert min_col == 0
    assert min_row == 0
    # Sanity: draw_ground actually blit tiles at all (not an empty range).
    assert len(fake_surface.calls) > 0


def test_ground_tile_screen_position_moves_right_as_col_increases_only():
    # The ground must scroll the same straight way as every other entity
    # (Camera.apply maps world x -> screen x independently of y) — col
    # increasing should shift screen_x only, never screen_y.
    origin = tile_geometry.ground_tile_screen_pos(0, 0, tile_width=64, tile_height=32, world_row=0)
    next_col = tile_geometry.ground_tile_screen_pos(1, 0, tile_width=64, tile_height=32, world_row=0)
    assert next_col[0] > origin[0]
    assert next_col[1] == origin[1]


def test_ground_tile_screen_position_moves_down_as_row_increases_on_the_same_world_row_parity():
    # Same for row -> screen_y: a pure-vertical camera/player movement
    # must not shift the ground horizontally (this was the reported bug —
    # moving straight up/down/left/right looked rotated 45 degrees because
    # the previous true-isometric formula mixed col and row into both axes).
    # Held to world_row=0 for both calls so the brick stagger (tested
    # separately below) doesn't also shift screen_x here.
    origin = tile_geometry.ground_tile_screen_pos(0, 0, tile_width=64, tile_height=32, world_row=0)
    next_row = tile_geometry.ground_tile_screen_pos(0, 1, tile_width=64, tile_height=32, world_row=0)
    assert next_row[0] == origin[0]
    assert next_row[1] > origin[1]


def test_ground_tile_screen_position_staggers_odd_world_rows_by_half_a_tile_width():
    # The diamond tile art needs a brick-course offset every other row to
    # interlock cleanly — without it, rows stack directly on top of each
    # other and the diamonds overlap into a wavy, scalloped mess.
    even_row = tile_geometry.ground_tile_screen_pos(0, 0, tile_width=64, tile_height=32, world_row=0)
    odd_row = tile_geometry.ground_tile_screen_pos(0, 0, tile_width=64, tile_height=32, world_row=1)
    assert odd_row[0] == even_row[0] + 32


def test_ground_tile_screen_position_stagger_is_fixed_to_the_world_grid():
    # The stagger must be keyed off the tile's absolute world row, not a
    # camera-relative value — otherwise it would flicker between offsets
    # as the camera scrolls smoothly instead of staying locked to the
    # same physical tiles.
    pos_a = tile_geometry.ground_tile_screen_pos(0, 2.3, tile_width=64, tile_height=32, world_row=5)
    pos_b = tile_geometry.ground_tile_screen_pos(0, 2.3, tile_width=64, tile_height=32, world_row=7)
    assert pos_a[0] == pos_b[0]


def test_is_border_tile_true_for_a_column_inside_the_border_zone():
    from game.config import WORLD_BORDER

    # A col near world (0,0) — well within the border band — is a border tile.
    assert tile_geometry.is_border_tile(col=0, row=10, tile_width=64, half_h=24) is True


def test_is_border_tile_false_for_a_column_well_inside_the_playable_area():
    from game.config import WORLD_BORDER, WORLD_WIDTH

    mid_col = int((WORLD_WIDTH / 2) / 64)
    assert tile_geometry.is_border_tile(col=mid_col, row=10, tile_width=64, half_h=24) is False


def test_is_border_tile_true_near_the_far_world_edge():
    from game.config import WORLD_WIDTH

    far_col = int(WORLD_WIDTH / 64) - 1
    assert tile_geometry.is_border_tile(col=far_col, row=10, tile_width=64, half_h=24) is True


def test_screen_pos_to_tile_inverts_ground_tile_screen_pos_at_origin_camera():
    from game.rendering.tile_geometry import TILE_WIDTH, TILE_FOOTPRINT_HEIGHT

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = 0, 0

    for col, row in [(0, 0), (5, 3), (12, 4), (20, 11)]:
        sx, sy = tile_geometry.ground_tile_screen_pos(col, row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=row)
        # click near the tile's own center, not its bounding box's corner
        click_x, click_y = sx + TILE_WIDTH / 2, sy + TILE_FOOTPRINT_HEIGHT / 4
        assert tile_geometry.screen_pos_to_tile(click_x, click_y, camera) == (col, row)


def test_screen_pos_to_tile_inverts_ground_tile_screen_pos_with_a_panned_camera():
    from game.rendering.tile_geometry import TILE_WIDTH, TILE_FOOTPRINT_HEIGHT

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = 640, 320

    cam_col = camera.x / TILE_WIDTH
    cam_row = camera.y / (TILE_FOOTPRINT_HEIGHT / 2)

    for col, row in [(10, 8), (15, 9), (30, 20)]:
        sx, sy = tile_geometry.ground_tile_screen_pos(col - cam_col, row - cam_row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=row)
        click_x, click_y = sx + TILE_WIDTH / 2, sy + TILE_FOOTPRINT_HEIGHT / 4
        assert tile_geometry.screen_pos_to_tile(click_x, click_y, camera) == (col, row)


def test_screen_pos_to_tile_accounts_for_odd_row_stagger():
    from game.rendering.tile_geometry import TILE_WIDTH, TILE_FOOTPRINT_HEIGHT

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = 0, 0

    # An odd world row is staggered half a tile width to the right —
    # inversion must account for that before recovering col.
    sx, sy = tile_geometry.ground_tile_screen_pos(7, 3, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=3)
    click_x, click_y = sx + TILE_WIDTH / 2, sy + TILE_FOOTPRINT_HEIGHT / 4
    assert tile_geometry.screen_pos_to_tile(click_x, click_y, camera) == (7, 3)


class _SurfaceIdentityRecordingSurface:
    """Records the exact blitted Surface object (by identity), not just
    its size — stone and grass tiles are the same pixel dimensions, so
    size alone can't distinguish which tile was actually drawn."""

    def __init__(self):
        self.blitted_surfaces = []

    def blit(self, source, dest):
        self.blitted_surfaces.append(source)

    def fill(self, color):
        pass


def test_draw_ground_uses_the_stone_tile_in_the_border_zone():
    from game.rendering.isometric_assets import get_stone_tile

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = 0, 0  # world's top-left corner, deep in the border

    fake_surface = _SurfaceIdentityRecordingSurface()
    ground.draw_ground(fake_surface, camera)

    assert get_stone_tile() in fake_surface.blitted_surfaces


def test_draw_ground_uses_the_grass_tile_away_from_the_border():
    from game.rendering.isometric_assets import get_grass_tile

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.x, camera.y = WORLD_WIDTH / 2, WORLD_HEIGHT / 2  # deep in the playable area

    fake_surface = _SurfaceIdentityRecordingSurface()
    ground.draw_ground(fake_surface, camera)

    assert get_grass_tile() in fake_surface.blitted_surfaces
    assert all(s is get_grass_tile() for s in fake_surface.blitted_surfaces)


def test_draw_ground_border_is_visible_when_the_camera_reaches_the_true_world_edge():
    # Regression: the ground's world-to-screen mapping must match
    # Camera.apply's (world_x - camera.x, no extra centering term) — an
    # earlier stray "+ WIDTH/2 - half_w" offset shifted every tile ~850px
    # off from where entities actually render, invisible against uniform
    # grass but making the border band land far outside the viewport
    # even when the camera's clamped position puts the true world edge
    # exactly at the screen's edge.
    from game.rendering.isometric_assets import get_stone_tile

    camera = Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)
    camera.snap_to(WORLD_WIDTH, WORLD_HEIGHT)  # clamps to the max reachable position

    fake_surface = _SurfaceIdentityRecordingSurface()
    ground.draw_ground(fake_surface, camera)

    assert get_stone_tile() in fake_surface.blitted_surfaces


def test_draw_overlay(surface, camera):
    entities.draw_overlay(surface, [Bomb(100, 100)], camera)


def test_draw_hud(surface, fonts):
    font, small_font = fonts
    hud.draw_hud(surface, font, small_font, score=10, high_score=20, bombs_left=2, lives=3, bomb_cooldown=0)


def test_draw_hud_with_no_bombs_mid_cooldown_and_one_life(surface, fonts):
    font, small_font = fonts
    hud.draw_hud(surface, font, small_font, score=0, high_score=0, bombs_left=0, lives=1, bomb_cooldown=600)


def _brightness(color):
    return sum(color[:3]) / 3


BRIGHT_GROUND = (235, 235, 235)


def test_draw_hud_puts_the_stats_on_a_dark_panel(surface, fonts):
    # Readability: the stats must sit on their own dark backing, not
    # straight on top of the (bright, busy) grass.
    font, small_font = fonts
    surface.fill(BRIGHT_GROUND)
    panel = hud.draw_hud(surface, font, small_font, score=10, high_score=20, bombs_left=2, lives=3, bomb_cooldown=0)

    # Left padding, vertically centered: inside the panel but clear of text.
    assert _brightness(surface.get_at((panel.x + 3, panel.centery))) < 100
    assert _brightness(surface.get_at((panel.right + 5, panel.centery))) == _brightness(BRIGHT_GROUND)


def test_draw_hud_puts_the_controls_hint_on_a_full_width_bottom_strip(surface, fonts):
    font, small_font = fonts
    surface.fill(BRIGHT_GROUND)
    hud.draw_hud(surface, font, small_font, score=10, high_score=20, bombs_left=2, lives=3, bomb_cooldown=0)

    for x in (2, WIDTH // 2, WIDTH - 3):
        assert _brightness(surface.get_at((x, HEIGHT - 2))) < 100
    assert _brightness(surface.get_at((WIDTH // 2, HEIGHT // 2))) == _brightness(BRIGHT_GROUND)


def test_draw_menu(surface, fonts):
    font, small_font = fonts
    hud.draw_menu(surface, font, small_font, ["Start Game", "Load Game", "Quit"], selected=0)


def test_draw_game_over_overlay(surface, fonts):
    font, small_font = fonts
    hud.draw_game_over_overlay(surface, font, small_font)


def test_bomb_is_drawn_at_its_body_radius_with_depth_scaling():
    # bomb.rect is the blast area, so the drawn size comes from body_radius.
    bomb = Bomb(500, 500)
    mid_screen_y = HEIGHT / 2
    expected = int(bomb.body_radius * entities.depth_scale_for(mid_screen_y))
    assert entities.bomb_body_radius(bomb, mid_screen_y) == expected


def test_explosion_effect_sprite_size_caps_at_a_scaled_maximum(camera):
    fake_surface = _BlitRecordingSurface()
    entities.draw_explosion_effect(fake_surface, ExplosionEffect(500, 500, radius=10_000), camera)
    size, _ = fake_surface.captured
    expected = entities.EXPLOSION_SPRITE_BASE_MAX_SIZE * ENTITY_SCALE
    assert size == (expected, expected)


def test_explosion_effect_sprite_size_floors_at_a_scaled_minimum(camera):
    fake_surface = _BlitRecordingSurface()
    entities.draw_explosion_effect(fake_surface, ExplosionEffect(500, 500, radius=1), camera)
    size, _ = fake_surface.captured
    expected = entities.EXPLOSION_SPRITE_BASE_MIN_SIZE * ENTITY_SCALE
    assert size == (expected, expected)


def _hurt_enemy(hp):
    enemy = Enemy("left", 500, 500)
    enemy.type = "elite"
    enemy.max_hp = 3
    enemy.hp = hp
    enemy.vx = 2.2
    return enemy


def test_draw_enemy_leaves_an_unhurt_critters_colors_alone(camera, colored_critter_frames):
    assert _drawn_color(_hurt_enemy(hp=3), camera) == (100, 0, 0)


def _blend(channel, target, t):
    return channel * (1 - t) + target * t


@pytest.mark.parametrize("base", [(200, 200, 200), (30, 40, 50)])
def test_draw_enemy_blends_a_hurt_critter_toward_injury_red(monkeypatch, camera, base):
    # A multiply-only tint just blackens dark art (the boar), so hurt
    # critters blend toward a fixed red instead: light and dark art alike
    # end up reading red.
    frames = {c: {f: [_solid_frame(base)] for f in ("SE", "SW")} for c in ("badger", "boar", "stag")}
    monkeypatch.setattr(entities, "get_critter_frames", lambda: frames)

    for hp, injury in ((2, 0.5), (1, 1.0)):
        t = entities.ENEMY_INJURY_TINT * injury
        drawn = _drawn_color(_hurt_enemy(hp=hp), camera)
        for channel, base_channel, red_channel in zip(drawn, base, entities.ENEMY_INJURY_RED):
            assert channel == pytest.approx(_blend(base_channel, red_channel, t), abs=2)

    last = _drawn_color(_hurt_enemy(hp=1), camera)
    assert last[0] > last[1] and last[0] > last[2]


def test_injury_tint_keeps_transparent_pixels_transparent():
    frame = pygame.Surface((4, 4), pygame.SRCALPHA)
    frame.fill((200, 200, 200, 0))
    frame.set_at((0, 0), (200, 200, 200, 255))
    tinted = entities._tinted(frame, 1.0)
    assert tinted.get_at((1, 1)).a == 0
    assert tinted.get_at((0, 0)).a == 255


def test_injury_tint_is_cached_per_frame_and_injury():
    frame = _solid_frame((200, 200, 200))
    assert entities._tinted(frame, 0.5) is entities._tinted(frame, 0.5)
    assert entities._tinted(frame, 0.5) is not entities._tinted(frame, 1.0)


class _AllBlitsSurface:
    def __init__(self):
        self.blits = []

    def fill(self, color):
        pass

    def blit(self, source, dest):
        self.blits.append((source, (round(dest[0]), round(dest[1]))))


def test_draw_ground_draws_the_ground_maps_tiles_inside_the_border(monkeypatch, camera):
    from game.simulation.tilemap import TileMap

    marker = pygame.Surface((tile_geometry.TILE_WIDTH, tile_geometry.TILE_HEIGHT))
    stone = pygame.Surface((tile_geometry.TILE_WIDTH, tile_geometry.TILE_HEIGHT))
    meadow = pygame.Surface((tile_geometry.TILE_WIDTH, tile_geometry.TILE_HEIGHT))
    monkeypatch.setattr(ground, "get_tile", lambda tile_id: marker)
    monkeypatch.setattr(ground, "get_stone_tile", lambda: stone)
    monkeypatch.setattr(ground, "get_grass_tile", lambda: meadow)

    camera.snap_to(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
    tilemap = TileMap(1, 1)
    min_col, max_col, min_row, max_row = tile_geometry.visible_tile_range(camera)
    for col in range(int(min_col), int(max_col)):
        for row in range(int(min_row), int(max_row)):
            tilemap.set_tile(col, row, "tile_000")

    fake = _AllBlitsSurface()
    ground.draw_ground(fake, camera, tilemap)
    drawn = {id(source) for source, _ in fake.blits}
    assert id(marker) in drawn
    assert id(meadow) not in drawn


def test_draw_ground_keeps_the_stone_border_and_meadow_without_a_map(monkeypatch, camera):
    stone = pygame.Surface((tile_geometry.TILE_WIDTH, tile_geometry.TILE_HEIGHT))
    meadow = pygame.Surface((tile_geometry.TILE_WIDTH, tile_geometry.TILE_HEIGHT))
    monkeypatch.setattr(ground, "get_stone_tile", lambda: stone)
    monkeypatch.setattr(ground, "get_grass_tile", lambda: meadow)

    camera.snap_to(0, 0)  # top-left corner: border and interior both visible
    fake = _AllBlitsSurface()
    ground.draw_ground(fake, camera)
    drawn = {id(source) for source, _ in fake.blits}
    assert drawn == {id(stone), id(meadow)}
