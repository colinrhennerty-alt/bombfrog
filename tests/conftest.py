import os

# Run pygame headlessly so importing main.py doesn't require a real display
# or open a window during test discovery/collection.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

# Surface.convert_alpha() (used by game.assets' sprite loader) raises
# "No video mode has been set" without an active display. Set one dummy
# mode once for the whole test session so no individual test needs to.
pygame.init()
pygame.display.set_mode((1, 1))
