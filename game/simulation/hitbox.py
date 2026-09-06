from game.simulation.rect import Rect


def sync_rect(x, y, width, height):
    """A collision box anchored at the same bottom-center point rendering
    draws the sprite at — so the hitbox always matches what's on screen."""
    return Rect.from_midbottom(x + width / 2, y + height, width, height)
