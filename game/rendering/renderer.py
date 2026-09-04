"""Pixel output for the game: "surface + state -> pixels" only.

Nothing here mutates game state; game.simulation owns that. Keeping
drawing separate means entity/world logic tests never need a display
surface, and this module can change purely visual behavior (camera
translation, shadows) without risking gameplay logic.
"""

import math

import pygame

from game.config import WIDTH, HEIGHT, BOMB_FUSE_MS
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy
from game.rendering.assets import get_frog_frames


def draw_shadow(surface, x, y, base_radius):
    # Draw a simple blurred shadow beneath the entity, in screen space
    # (caller has already applied the camera translation).
    sr = max(6, int(base_radius * 0.6))
    shadow = pygame.Surface((sr * 2, int(sr * 0.6)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, sr * 2, int(sr * 0.6)))
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


def draw_bomb(surface, bomb, camera):
    sx, sy = camera.apply(bomb.x, bomb.y)
    sy += bomb.fall_offset
    r = 14
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
    pygame.draw.circle(surface, shard.color, (int(sx), int(sy)), shard.radius)


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
        sx, sy = camera.apply(entity.x, entity.y)
        draw_shadow(surface, sx, sy, base_radius)

    for entity in drawables:
        draw_func = _DRAW_FUNCS.get(type(entity))
        if draw_func:
            draw_func(surface, entity, camera)

    for effect in effects:
        draw_explosion_effect(surface, effect, camera)


def draw_ground(surface, camera):
    surface.fill((52, 88, 58))
    tile = 120
    offset_x = int(-camera.x) % tile
    offset_y = int(-camera.y) % tile
    for gx in range(offset_x - tile, WIDTH + tile, tile):
        pygame.draw.line(surface, (44, 74, 48), (gx, 0), (gx, HEIGHT), 1)
    for gy in range(offset_y - tile, HEIGHT + tile, tile):
        pygame.draw.line(surface, (44, 74, 48), (0, gy), (WIDTH, gy), 1)


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
