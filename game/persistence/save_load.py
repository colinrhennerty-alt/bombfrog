import json
import os


def save_game(filename, player, bombs, shards, enemies, score, high_score, lives, last_spawn):
    state = {
        "player": player.to_dict(),
        "bombs": [bomb.to_dict() for bomb in bombs],
        "shards": [shard.to_dict() for shard in shards],
        "enemies": [enemy.to_dict() for enemy in enemies],
        "score": score,
        "high_score": high_score,
        "lives": lives,
        "last_spawn": last_spawn,
    }
    with open(filename, "w") as handle:
        json.dump(state, handle)


def load_game(filename):
    if not os.path.exists(filename):
        return None
    with open(filename, "r") as handle:
        return json.load(handle)
