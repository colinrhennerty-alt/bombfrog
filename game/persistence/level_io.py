import json
import os

from game.simulation.tilemap import TileMap


def save_level(filename, tilemap):
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w") as handle:
        json.dump(tilemap.to_dict(), handle)


def load_level(filename):
    if not os.path.exists(filename):
        return None
    with open(filename, "r") as handle:
        return TileMap.from_dict(json.load(handle))
