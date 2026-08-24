import pygame

from game.simulation.depth import scale_for_depth


def sync_rect_for_depth(x, y, width, height, depth):
    """A collision box scaled to match the depth-scaled visual size,
    anchored at the same bottom-center point rendering draws the
    sprite at — so the hitbox always matches what's on screen, at any
    depth."""
    scale = scale_for_depth(depth)
    w = max(1, int(width * scale))
    h = max(1, int(height * scale))
    rect = pygame.Rect(0, 0, w, h)
    rect.midbottom = (x + width / 2, y + height)
    return rect
