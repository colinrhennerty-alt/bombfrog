import main


def test_load_game_returns_none_when_file_missing(tmp_path):
    missing_file = tmp_path / "does-not-exist.json"
    assert main.load_game(str(missing_file)) is None


def test_save_and_load_round_trip(tmp_path):
    save_path = tmp_path / "save.json"

    player = main.Player()
    player.x, player.y = 123, 45
    player.vx, player.vy = 1, -2
    player.bombs_left = 1
    player.pending_bomb = True
    player.bomb_cooldown = 250

    bombs = [main.Bomb(10, 20)]
    shards = [main.Shard(30, 40, angle=0, speed=5)]
    enemies = [main.Enemy("left")]

    main.save_game(str(save_path), player, bombs, shards, enemies, score=42, high_score=99, lives=2, last_spawn=777)

    loaded = main.load_game(str(save_path))

    assert loaded["player"]["x"] == 123
    assert loaded["player"]["y"] == 45
    assert loaded["player"]["vx"] == 1
    assert loaded["player"]["vy"] == -2
    assert loaded["player"]["bombs_left"] == 1
    assert loaded["player"]["pending_bomb"] is True
    assert loaded["player"]["bomb_cooldown"] == 250

    assert len(loaded["bombs"]) == 1
    assert loaded["bombs"][0]["x"] == 10
    assert loaded["bombs"][0]["y"] == 20

    assert len(loaded["shards"]) == 1
    assert len(loaded["enemies"]) == 1
    assert loaded["enemies"][0]["type"] == enemies[0].type

    assert loaded["score"] == 42
    assert loaded["high_score"] == 99
    assert loaded["lives"] == 2
    assert loaded["last_spawn"] == 777


def test_enemy_from_dict_restores_state():
    enemy = main.Enemy("left")
    enemy.x, enemy.y, enemy.vx = 111, 222, -2.2
    enemy.dead = False
    enemy.hp = 2

    restored = main.Enemy.from_dict(
        {
            "x": enemy.x,
            "y": enemy.y,
            "vx": enemy.vx,
            "type": enemy.type,
            "dead": enemy.dead,
            "hp": enemy.hp,
        }
    )

    assert restored.x == 111
    assert restored.y == 222
    assert restored.vx == -2.2
    assert restored.type == enemy.type
    assert restored.dead is False
    assert restored.hp == 2
