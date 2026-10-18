"""Screen-space text and overlays: the in-game HUD, the main menu, and the
game-over screen."""

import pygame

from game.config import WIDTH, HEIGHT, BOMB_LIMIT, BOMB_COOLDOWN_MS, STARTING_LIVES
from game.simulation.enemy_types import ENEMY_TYPES
from game.rendering.assets import get_critter_frames

# Every HUD element sits on this translucent dark backing so it reads on
# top of the bright, busy grass (tests/test_renderer.py checks this).
PANEL_COLOR = (12, 18, 28, 215)
PANEL_MARGIN = 16
PANEL_PADDING = 14
PANEL_RADIUS = 10
ROW_GAP = 8
SECTION_GAP = 14

TEXT_COLOR = (245, 245, 245)
LABEL_COLOR = (165, 178, 196)
BOMB_COLOR = (255, 196, 92)
LIFE_COLOR = (255, 104, 120)
EMPTY_PIP_COLOR = (90, 100, 115)
DIVIDER_COLOR = (60, 70, 86)
# The critter art is dark; a light chip behind each legend icon keeps it
# visible on the dark panel.
ICON_CHIP_COLOR = (150, 162, 180)
KEY_COLOR = (255, 214, 120)

PIP_RADIUS = 7
PIP_GAP = 6
LABEL_WIDTH = 64  # stat labels share one column so their pips line up
COOLDOWN_BAR_SIZE = (100, 6)
LEGEND_ICON_SIZE = 30

CONTROLS_HINT = (
    ("SPACE", "jump (drops a bomb)"),
    ("ARROWS / WASD", "move"),
    ("F5", "save"),
    ("F9", "load"),
    ("ESC", "menu"),
)
CONTROLS_KEY_GAP = 8
CONTROLS_ENTRY_GAP = 32


def _translucent_rect(surface, rect, radius):
    backing = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(backing, PANEL_COLOR, backing.get_rect(), border_radius=radius)
    surface.blit(backing, rect.topleft)


class _Row:
    """One HUD line: measured up front so the panel can be sized before
    anything is drawn on it."""

    def __init__(self, width, height, draw):
        self.width, self.height, self.draw = width, height, draw


def _text_row(text):
    return _Row(text.get_width(), text.get_height(), lambda s, x, y: s.blit(text, (x, y)))


def _pip_row(small_font, label, filled, total, color, extra=None):
    """A label followed by `total` pips, the first `filled` of them solid.
    `extra` optionally draws something under the pips (the cooldown bar)."""
    text = small_font.render(label, True, LABEL_COLOR)
    pip = PIP_RADIUS * 2
    pips_width = total * pip + (total - 1) * PIP_GAP
    height = max(text.get_height(), pip) + (extra[1] + 4 if extra else 0)

    def draw(surface, x, y):
        surface.blit(text, (x, y + (pip - text.get_height()) // 2))
        pip_x = x + LABEL_WIDTH
        for i in range(total):
            center = (pip_x + PIP_RADIUS + i * (pip + PIP_GAP), y + PIP_RADIUS)
            if i < filled:
                pygame.draw.circle(surface, color, center, PIP_RADIUS)
            else:
                pygame.draw.circle(surface, EMPTY_PIP_COLOR, center, PIP_RADIUS, 2)
        if extra:
            extra[2](surface, pip_x, y + pip + 4)

    width = LABEL_WIDTH + max(pips_width, extra[0] if extra else 0)
    return _Row(width, height, draw)


def _cooldown_bar(bomb_cooldown):
    """(width, height, draw): a bar that fills as the next bomb recharges,
    and is full when one is ready."""
    width, height = COOLDOWN_BAR_SIZE
    ready_fraction = 1 - max(0, min(1, bomb_cooldown / BOMB_COOLDOWN_MS))

    def draw(surface, x, y):
        pygame.draw.rect(surface, EMPTY_PIP_COLOR, (x, y, width, height), border_radius=3)
        if ready_fraction > 0:
            pygame.draw.rect(surface, BOMB_COLOR, (x, y, int(width * ready_fraction), height), border_radius=3)

    return width, height, draw


def _legend_row(small_font, enemy_type):
    """The critter's own art next to its name, so the legend matches what's
    actually on screen."""
    frame = get_critter_frames()[enemy_type.sprite]["SW"][0]
    scale = (LEGEND_ICON_SIZE - 4) / max(frame.get_size())
    icon = pygame.transform.scale(frame, (round(frame.get_width() * scale), round(frame.get_height() * scale)))
    name = small_font.render(enemy_type.name.capitalize(), True, TEXT_COLOR)
    hp = small_font.render(f"{enemy_type.max_hp} HP", True, LABEL_COLOR)
    name_x = LEGEND_ICON_SIZE + 10
    hp_x = name_x + 70

    def draw(surface, x, y):
        pygame.draw.rect(surface, ICON_CHIP_COLOR, (x, y, LEGEND_ICON_SIZE, LEGEND_ICON_SIZE), border_radius=6)
        surface.blit(icon, (x + (LEGEND_ICON_SIZE - icon.get_width()) // 2, y + (LEGEND_ICON_SIZE - icon.get_height()) // 2))
        text_y = y + (LEGEND_ICON_SIZE - name.get_height()) // 2
        surface.blit(name, (x + name_x, text_y))
        surface.blit(hp, (x + hp_x, text_y))

    return _Row(hp_x + hp.get_width(), LEGEND_ICON_SIZE, draw)


def _divider_row(width):
    return _Row(width, 1, lambda s, x, y: pygame.draw.line(s, DIVIDER_COLOR, (x, y), (x + width, y)))


def _draw_stats_panel(surface, font, small_font, score, high_score, bombs_left, lives, bomb_cooldown):
    stats = [
        _text_row(font.render(f"{score:,}", True, TEXT_COLOR)),
        _text_row(small_font.render(f"Best  {max(score, high_score):,}", True, LABEL_COLOR)),
        _pip_row(small_font, "Lives", lives, max(lives, STARTING_LIVES), LIFE_COLOR),
        _pip_row(small_font, "Bombs", bombs_left, BOMB_LIMIT, BOMB_COLOR, extra=_cooldown_bar(bomb_cooldown)),
    ]
    legend = [_legend_row(small_font, enemy_type) for enemy_type in ENEMY_TYPES.values()]
    content_width = max(row.width for row in stats + legend)
    sections = [stats, [_divider_row(content_width)], legend]

    content_height = sum(row.height for section in sections for row in section)
    content_height += sum(ROW_GAP * (len(section) - 1) for section in sections)
    content_height += SECTION_GAP * (len(sections) - 1)
    panel = pygame.Rect(
        PANEL_MARGIN, PANEL_MARGIN, content_width + 2 * PANEL_PADDING, content_height + 2 * PANEL_PADDING,
    )
    _translucent_rect(surface, panel, PANEL_RADIUS)

    x, y = panel.x + PANEL_PADDING, panel.y + PANEL_PADDING
    for section in sections:
        for row in section:
            row.draw(surface, x, y)
            y += row.height + ROW_GAP
        y += SECTION_GAP - ROW_GAP
    return panel


def _draw_controls_strip(surface, small_font):
    """Key names highlighted, descriptions muted, laid out as one centered line."""
    pieces = []  # (surface, gap after it)
    for key, description in CONTROLS_HINT:
        pieces.append((small_font.render(key, True, KEY_COLOR), CONTROLS_KEY_GAP))
        pieces.append((small_font.render(description, True, TEXT_COLOR), CONTROLS_ENTRY_GAP))
    line_height = max(text.get_height() for text, _ in pieces)
    line_width = sum(text.get_width() + gap for text, gap in pieces) - pieces[-1][1]

    strip = pygame.Rect(0, HEIGHT - line_height - 16, WIDTH, line_height + 16)
    _translucent_rect(surface, strip, 0)
    x = strip.centerx - line_width // 2
    for text, gap in pieces:
        surface.blit(text, (x, strip.centery - text.get_height() // 2))
        x += text.get_width() + gap


def draw_hud(surface, font, small_font, score, high_score, bombs_left, lives, bomb_cooldown):
    """The stats panel (top-left) and controls strip (bottom). Returns the
    stats panel's rect."""
    panel = _draw_stats_panel(surface, font, small_font, score, high_score, bombs_left, lives, bomb_cooldown)
    _draw_controls_strip(surface, small_font)
    return panel


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
