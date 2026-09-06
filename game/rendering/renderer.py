"""Pixel output for the game: "surface + state -> pixels" only.

Nothing here mutates game state; game.simulation owns that. Keeping
drawing separate means entity/world logic tests never need a display
surface, and this module can change purely visual behavior (camera
translation, shadows) without risking gameplay logic.
"""

import math

import pygame

from game.config import WIDTH, HEIGHT, BOMB_FUSE_MS
from game.utils import clamp
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy
from game.rendering.assets import get_frog_frames
from game.rendering.isometric_assets import get_grass_tile, TILE_WIDTH, TILE_HEIGHT, TILE_FOOTPRINT_HEIGHT


def shadow_size_for(base_radius, height_offset):
    """Shrink the shadow as the entity rises off the ground, so height
    reads visually even though the sim is pure 2D. height_offset is the
    same jump_offset/fall_offset magnitude used to draw the entity itself
    (0 = grounded, larger magnitude = higher up)."""
    shrink = 1 / (1 + abs(height_offset) / 60)
    return max(6, int(base_radius * 0.6 * shrink))


def draw_shadow(surface, x, y, base_radius, height_offset=0):
    # Draw a simple blurred shadow beneath the entity, in screen space
    # (caller has already applied the camera translation).
    sr = shadow_size_for(base_radius, height_offset)
    alpha = max(30, int(90 * (1 / (1 + abs(height_offset) / 60))))
    shadow = pygame.Surface((sr * 2, int(sr * 0.6)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, 0, sr * 2, int(sr * 0.6)))
    surface.blit(shadow, (int(x) - sr, int(y) - int(sr * 0.3)))


def draw_player(surface, player, camera):
    frames = get_frog_frames()
    if not player.on_ground:
        frame = frames["jump"]
    elif player.land_timer > 0:
        frame = frames["land"]
    else:
        frame = frames["idle"][player.anim_index]

    if player.facing > 0:
        frame = pygame.transform.flip(frame, True, False)

    # Scale to the collision rect's own size, not the spritesheet's native
    # cell size, so the drawn sprite and the hitbox always match exactly.
    frame = pygame.transform.smoothscale(frame, player.rect.size)
    screen_rect = camera.apply_rect(player.rect)
    screen_rect.y += int(player.jump_offset)
    surface.blit(frame, screen_rect.topleft)


def depth_scale_for(screen_y):
    """A cheap perspective-camera trick: entities nearer the top of the
    viewport read smaller, entities nearer the bottom read larger, as if
    the camera were looking down at an angle instead of straight down."""
    return 0.85 + 0.3 * clamp(screen_y / HEIGHT, 0, 1)


def draw_bomb(surface, bomb, camera):
    sx, sy = camera.apply(bomb.x, bomb.y)
    sy += bomb.fall_offset
    r = int(14 * depth_scale_for(sy))
    pygame.draw.circle(surface, bomb.color, (int(sx), int(sy)), r)
    fuse_ratio = max(0, bomb.timer / BOMB_FUSE_MS)
    arc_r = 20
    arc_rect = (sx - arc_r, sy - arc_r, arc_r * 2, arc_r * 2)
    pygame.draw.arc(surface, (255, 240, 120), arc_rect, math.pi * 0.5, math.pi * 0.5 + math.pi * 2 * fuse_ratio, 4)


def draw_bomb_explosion_radius(surface, bomb, camera):
    sx, sy = camera.apply(bomb.x, bomb.y)
    pygame.draw.circle(surface, (255, 180, 0, 40), (int(sx), int(sy)), bomb.radius, 2)


def draw_shard(surface, shard, camera):
    sx, sy = camera.apply(shard.x, shard.y)
    r = max(1, int(shard.radius * depth_scale_for(sy)))
    pygame.draw.circle(surface, shard.color, (int(sx), int(sy)), r)


def draw_enemy(surface, enemy, camera):
    # enemy.rect is already sized/positioned in world space — draw exactly
    # into its camera-translated screen rect so the body and hitbox match.
    screen_rect = camera.apply_rect(enemy.rect)
    pygame.draw.rect(surface, enemy.color, screen_rect, border_radius=8)
    if enemy.type == "elite":
        pygame.draw.circle(surface, (255, 255, 255), screen_rect.center, 6)


def draw_explosion_effect(surface, effect, camera):
    sx, sy = camera.apply(effect.x, effect.y)
    alpha = int(180 * max(0, effect.life / 260))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(overlay, (255, 180, 60, alpha), (int(sx), int(sy)), max(4, int(effect.radius)), 4)
    surface.blit(overlay, (0, 0))


_DRAW_FUNCS = {
    Player: draw_player,
    Bomb: draw_bomb,
    Shard: draw_shard,
    Enemy: draw_enemy,
}

_DEBUG_BOX_COLORS = {
    Player: (0, 255, 0),
    Bomb: (255, 80, 80),
    Shard: (255, 255, 0),
    Enemy: (80, 160, 255),
}


def draw_debug_boxes(surface, player, bombs, shards, enemies, camera):
    """Outlines the exact .rect each entity uses for colliderect checks
    in game.world — not an approximation, the real hitbox."""
    entities = list(enemies) + list(bombs) + list(shards)
    if player:
        entities.append(player)
    for entity in entities:
        color = _DEBUG_BOX_COLORS.get(type(entity), (255, 255, 255))
        pygame.draw.rect(surface, color, camera.apply_rect(entity.rect), width=2)


def draw_scene(surface, player, bombs, shards, enemies, effects, camera):
    """Depth-sort everything by y, draw shadows, then sprites, then effects on top."""
    drawables = list(enemies) + list(bombs) + list(shards)
    if player:
        drawables.append(player)
    drawables.sort(key=lambda entity: entity.y)

    for entity in drawables:
        base_radius = getattr(entity, "radius", getattr(entity, "width", 20))
        height_offset = getattr(entity, "jump_offset", getattr(entity, "fall_offset", 0))
        sx, sy = camera.apply(entity.x, entity.y)
        draw_shadow(surface, sx, sy, base_radius, height_offset)

    for entity in drawables:
        draw_func = _DRAW_FUNCS.get(type(entity))
        if draw_func:
            draw_func(surface, entity, camera)

    for effect in effects:
        draw_explosion_effect(surface, effect, camera)


def iso_tile_screen_pos(col, row, tile_width, tile_height):
    """Standard isometric projection: a tile's (col, row) grid coordinate
    to its screen-space top-left offset, fanning out into a diamond grid
    (col increases right+down, row increases left+down)."""
    screen_x = (col - row) * (tile_width / 2)
    screen_y = (col + row) * (tile_height / 2)
    return screen_x, screen_y


def draw_ground(surface, camera):
    surface.fill((52, 88, 58))
    tile = get_grass_tile()
    half_w, half_h = TILE_WIDTH / 2, TILE_FOOTPRINT_HEIGHT / 2

    # World space maps 1:1 onto the (col, row) tile grid (one world-unit
    # square of ground per tile), then iso_tile_screen_pos fans that grid
    # into the diamond layout on screen. Spacing uses the diamond's own
    # footprint height, not the full sprite height (the sprite also draws
    # a "skirt" below the diamond face that neighboring tiles overlap).
    cam_col = camera.x / TILE_WIDTH
    cam_row = camera.y / TILE_WIDTH

    # The screen area a single (col, row) step can reach in either
    # direction is half_w + half_h; pad the visible range by that much on
    # every side so the diamond grid still covers the viewport's corners.
    pad_cols = int(WIDTH / (2 * half_w)) + 2
    pad_rows = int(HEIGHT / (2 * half_h)) + 2

    # Draw back-to-front (ascending row+col) so nearer tiles' sprites
    # correctly paint over farther tiles' skirts, like real isometric art.
    coords = [
        (col, row)
        for col in range(int(cam_col) - pad_cols, int(cam_col) + pad_cols)
        for row in range(int(cam_row) - pad_rows, int(cam_row) + pad_rows)
    ]
    coords.sort(key=lambda cr: cr[0] + cr[1])

    for col, row in coords:
        sx, sy = iso_tile_screen_pos(col - cam_col, row - cam_row, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT)
        sx += WIDTH / 2 - half_w
        sy += HEIGHT / 2 - half_h
        if sx + TILE_WIDTH >= 0 and sx <= WIDTH and sy + TILE_HEIGHT >= 0 and sy <= HEIGHT:
            surface.blit(tile, (sx, sy))


def draw_overlay(surface, bombs, camera):
    for bomb in bombs:
        if bomb.timer > 0:
            radius = int(bomb.radius * (1 - bomb.timer / BOMB_FUSE_MS) * 0.5 + 20)
            sx, sy = camera.apply(bomb.x, bomb.y)
            pygame.draw.circle(surface, (255, 170, 0, 40), (int(sx), int(sy)), radius, 1)


def draw_hud(surface, font, small_font, score, high_score, bombs_left, lives, bomb_cooldown):
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    high_text = small_font.render(f"High Score: {high_score}", True, (240, 240, 240))
    bomb_text = small_font.render(f"Bombs: {bombs_left}", True, (255, 220, 120))
    life_text = small_font.render(f"Lives: {lives}", True, (180, 210, 255))
    legend_title = small_font.render("Enemies:", True, (220, 220, 220))
    grunt_text = small_font.render("Grunt", True, (190, 80, 80))
    heavy_text = small_font.render("Heavy", True, (170, 130, 80))
    elite_text = small_font.render("Elite", True, (150, 95, 185))
    prompt_text = small_font.render(
        "SPACE = jump/save bomb | UP/DOWN = move | S=save | L=load | avoid shards", True, (210, 210, 210)
    )
    surface.blit(score_text, (20, 20))
    surface.blit(high_text, (20, 60))
    surface.blit(bomb_text, (20, 100))
    cooldown_text = small_font.render(f"Bomb CD: {max(0, int(bomb_cooldown / 1000 * 10) / 10):.1f}s", True, (255, 200, 120))
    surface.blit(life_text, (20, 140))
    surface.blit(cooldown_text, (20, 170))
    surface.blit(legend_title, (20, 210))
    pygame.draw.circle(surface, (190, 80, 80), (30, 210), 5)
    surface.blit(grunt_text, (45, 204))
    pygame.draw.circle(surface, (170, 130, 80), (30, 232), 5)
    surface.blit(heavy_text, (45, 226))
    pygame.draw.circle(surface, (150, 95, 185), (30, 254), 5)
    surface.blit(elite_text, (45, 248))
    surface.blit(prompt_text, (20, HEIGHT - 40))


def draw_menu(surface, font, small_font, menu_options, selected):
    title = font.render("Bomb Frog", True, (255, 255, 255))
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
    subtitle = small_font.render("Leapfrog with bombs — press Enter to select", True, (220, 220, 220))
    surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 130))

    for i, opt in enumerate(menu_options):
        color = (255, 220, 120) if i == selected else (200, 200, 200)
        text = font.render(opt, True, color)
        surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 220 + i * 60))

    hint = small_font.render("Use UP/DOWN to move, ENTER to confirm", True, (180, 180, 180))
    surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))


def draw_game_over_overlay(surface, font, small_font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    game_over_text = font.render("Game Over", True, (255, 220, 90))
    restart_text = small_font.render("Press SPACE or R to restart, ESC to quit.", True, (245, 245, 245))
    surface.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
    surface.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
