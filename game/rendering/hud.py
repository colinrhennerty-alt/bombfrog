"""Screen-space text and overlays: the in-game HUD, the main menu, and the
game-over screen."""

import pygame

from game.config import WIDTH, HEIGHT


def draw_hud(surface, font, small_font, score, high_score, bombs_left, lives, bomb_cooldown):
    # Lines are stacked from a running y cursor advanced by each font's own
    # linesize (plus a little breathing room) rather than hardcoded pixel
    # offsets, so the column never overlaps if a font's rendered glyph
    # height changes across platforms/fonts.
    line_gap = 6
    x = 20
    y = 20

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    surface.blit(score_text, (x, y))
    y += font.get_linesize() + line_gap

    small_line_height = small_font.get_linesize() + line_gap

    high_text = small_font.render(f"High Score: {high_score}", True, (240, 240, 240))
    surface.blit(high_text, (x, y))
    y += small_line_height

    bomb_text = small_font.render(f"Bombs: {bombs_left}", True, (255, 220, 120))
    surface.blit(bomb_text, (x, y))
    y += small_line_height

    life_text = small_font.render(f"Lives: {lives}", True, (180, 210, 255))
    surface.blit(life_text, (x, y))
    y += small_line_height

    cooldown_text = small_font.render(f"Bomb CD: {max(0, int(bomb_cooldown / 1000 * 10) / 10):.1f}s", True, (255, 200, 120))
    surface.blit(cooldown_text, (x, y))
    y += small_line_height + line_gap

    legend_title = small_font.render("Enemies:", True, (220, 220, 220))
    surface.blit(legend_title, (x, y))
    y += small_line_height

    legend_entries = (
        ("Grunt", (190, 80, 80)),
        ("Heavy", (170, 130, 80)),
        ("Elite", (150, 95, 185)),
    )
    for label, color in legend_entries:
        entry_text = small_font.render(label, True, color)
        pygame.draw.circle(surface, color, (x + 10, y + small_font.get_height() // 2), 5)
        surface.blit(entry_text, (x + 25, y))
        y += small_line_height

    prompt_text = small_font.render(
        "SPACE = jump (drops a bomb) | ARROWS/WASD = move | F5 = save | F9 = load | ESC = menu", True, (210, 210, 210)
    )
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
    restart_text = small_font.render("Press SPACE or R to restart, ESC for menu.", True, (245, 245, 245))
    surface.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
    surface.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
