"""Pixel output for the game: "surface + state -> pixels" only.

Nothing here mutates game state; game.entities/game.world own that. Keeping
drawing separate means entity/world logic tests never need a display
surface, and this module can change purely visual behavior (parallax,
depth scaling, shadows) without risking gameplay logic.
"""

import math

import pygame

from game.config import WIDTH, HEIGHT, GROUND_NEAR_Y, GROUND_FAR_Y, FAR_MARGIN, GROUND_HEIGHT, BOMB_FUSE_MS
from game.utils import clamp
from game.depth import ground_y_for_depth, margin_for_depth, scale_for_depth
from game.entities import Player, Bomb, Shard, Enemy
from game.assets import get_frog_frames


def draw_shadow(surface, x, y, ground_y, base_radius, scale):
    # Draw a simple blurred shadow projected onto the ground
    # shadow position anchored near ground under object
    sx = int(x)
    sy = int(ground_y) - int(6 * scale)
    sr = max(6, int(base_radius * scale * 0.6))
    shadow = pygame.Surface((sr * 2, int(sr * 0.6)), pygame.SRCALPHA)
    alpha = int(120 * clamp(1.0 - (y / float(ground_y)), 0.3, 1.0))
    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, 0, sr * 2, int(sr * 0.6)))
    surface.blit(shadow, (sx - sr, sy - int(sr * 0.3)))


def draw_player(surface, player):
    frames = get_frog_frames()
    if not player.on_ground:
        frame = frames["jump"]
    elif player.land_timer > 0:
        frame = frames["land"]
    else:
        frame = frames["idle"][player.anim_index]

    if player.facing > 0:
        frame = pygame.transform.flip(frame, True, False)

    size = (max(1, int(frame.get_width() * player.scale)), max(1, int(frame.get_height() * player.scale)))
    frame = pygame.transform.smoothscale(frame, size)

    sprite_rect = frame.get_rect(midbottom=(player.centerx, player.y + player.height))
    surface.blit(frame, sprite_rect)


def draw_bomb(surface, bomb):
    scale = bomb.scale
    r = max(4, int(14 * scale))
    pygame.draw.circle(surface, bomb.color, (int(bomb.x), int(bomb.y)), r)
    fuse_ratio = max(0, bomb.timer / BOMB_FUSE_MS)
    arc_r = max(4, int(20 * scale))
    arc_rect = (bomb.x - arc_r, bomb.y - arc_r, arc_r * 2, arc_r * 2)
    pygame.draw.arc(surface, (255, 240, 120), arc_rect, math.pi * 0.5, math.pi * 0.5 + math.pi * 2 * fuse_ratio, max(1, int(4 * scale)))


def draw_bomb_explosion_radius(surface, bomb):
    scale = bomb.scale
    pygame.draw.circle(surface, (255, 180, 0, 40), (int(bomb.x), int(bomb.y)), int(bomb.radius * scale), max(1, int(2 * scale)))


def draw_shard(surface, shard):
    pygame.draw.circle(surface, shard.color, (int(shard.x), int(shard.y)), shard.radius)


def draw_enemy(surface, enemy):
    scale = scale_for_depth(enemy.depth)
    w = max(1, int(enemy.width * scale))
    h = max(1, int(enemy.height * scale))
    draw_rect = pygame.Rect(0, 0, w, h)
    draw_rect.midbottom = enemy.rect.midbottom
    pygame.draw.rect(surface, enemy.color, draw_rect, border_radius=max(2, int(8 * scale)))
    if enemy.type == "elite":
        pygame.draw.circle(surface, (255, 255, 255), draw_rect.center, max(3, int(6 * scale)))


def draw_explosion_effect(surface, effect):
    alpha = int(180 * max(0, effect.life / 260))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(overlay, (255, 180, 60, alpha), (int(effect.x), int(effect.y)), max(4, int(effect.radius)), 4)
    surface.blit(overlay, (0, 0))


_DRAW_FUNCS = {
    Player: draw_player,
    Bomb: draw_bomb,
    Shard: draw_shard,
    Enemy: draw_enemy,
}


def draw_scene(surface, player, bombs, shards, enemies, effects):
    """Depth-sort everything by y, draw shadows, then sprites, then effects on top."""
    drawables = list(enemies) + list(bombs) + list(shards)
    if player:
        drawables.append(player)
    drawables.sort(key=lambda entity: entity.y)

    for entity in drawables:
        depth = getattr(entity, "depth", 1.0)
        base_radius = getattr(entity, "radius", getattr(entity, "width", 20))
        draw_shadow(surface, entity.x, entity.y, ground_y_for_depth(depth), base_radius, scale_for_depth(depth))

    for entity in drawables:
        draw_func = _DRAW_FUNCS.get(type(entity))
        if draw_func:
            draw_func(surface, entity)

    for effect in effects:
        draw_explosion_effect(surface, effect)


def draw_parallax_background(surface, cam_x):
    pygame.draw.rect(surface, (18, 30, 50), (0, 0, WIDTH, HEIGHT))
    m1_x = -int(cam_x * 0.12) % (WIDTH * 2)
    pygame.draw.ellipse(surface, (50, 60, 90), (m1_x - 300, 40, WIDTH + 600, 180))
    pygame.draw.ellipse(surface, (60, 70, 110), (m1_x + 200, 100, WIDTH, 140))
    m2_x = -int(cam_x * 0.24) % (WIDTH * 2)
    pygame.draw.ellipse(surface, (70, 50, 30), (m2_x - 200, GROUND_NEAR_Y - 80, WIDTH + 400, 160))


def draw_ground(surface):
    top_left = (FAR_MARGIN, GROUND_FAR_Y)
    top_right = (WIDTH - FAR_MARGIN, GROUND_FAR_Y)
    bottom_right = (WIDTH, GROUND_NEAR_Y)
    bottom_left = (0, GROUND_NEAR_Y)
    pygame.draw.polygon(surface, (52, 88, 58), [top_left, top_right, bottom_right, bottom_left])
    for t in (0.33, 0.66):
        y = ground_y_for_depth(t)
        m = margin_for_depth(t)
        pygame.draw.line(surface, (44, 74, 48), (m, y), (WIDTH - m, y), 2)

    pygame.draw.rect(surface, (90, 54, 20), (0, GROUND_NEAR_Y, WIDTH, GROUND_HEIGHT))
    for i in range(0, WIDTH, 80):
        pygame.draw.arc(surface, (77, 45, 16), (i, GROUND_NEAR_Y - 40, 80, 80), math.pi, 0, 4)


def draw_overlay(surface, bombs):
    for bomb in bombs:
        if bomb.timer > 0:
            radius = int(bomb.radius * (1 - bomb.timer / BOMB_FUSE_MS) * 0.5 + 20)
            pygame.draw.circle(surface, (255, 170, 0, 40), (int(bomb.x), int(bomb.y)), radius, 1)


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
        "SPACE = jump/save bomb | UP/DOWN = depth | S=save | L=load | avoid shards", True, (210, 210, 210)
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
