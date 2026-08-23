import json
import os


def save_game(filename, player, bombs, shards, enemies, score, high_score, lives, last_spawn):
    state = {
        "player": {
            "x": player.x,
            "y": player.y,
            "vx": player.vx,
            "vy": player.vy,
            "depth": player.depth,
            "on_ground": player.on_ground,
            "bombs_left": player.bombs_left,
            "pending_bomb": player.pending_bomb,
            "bomb_cooldown": player.bomb_cooldown,
        },
        "bombs": [
            {
                "x": bomb.x,
                "y": bomb.y,
                "depth": bomb.depth,
                "timer": bomb.timer,
                "has_shrapnel": bomb.has_shrapnel,
            }
            for bomb in bombs
        ],
        "shards": [
            {
                "x": shard.x,
                "y": shard.y,
                "vx": shard.vx,
                "vy": shard.vy,
                "life": shard.life,
                "color": list(shard.color),
            }
            for shard in shards
        ],
        "enemies": [
            {
                "x": enemy.x,
                "y": enemy.y,
                "vx": enemy.vx,
                "type": enemy.type,
                "depth": enemy.depth,
                "dead": enemy.dead,
                "hp": enemy.hp,
            }
            for enemy in enemies
        ],
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
