import pygame


def sync_rect(x, y, width, height):
    """A collision box anchored at the same bottom-center point rendering
    draws the sprite at — so the hitbox always matches what's on screen."""
    rect = pygame.Rect(0, 0, width, height)
    rect.midbottom = (x + width / 2, y + height)
    return rect
