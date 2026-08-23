import os

# Run pygame headlessly so importing main.py doesn't require a real display
# or open a window during test discovery/collection.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
