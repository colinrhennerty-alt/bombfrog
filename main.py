import json
import math
import os
import random
import sys
import pygame

from game.config import (
    WIDTH,
    HEIGHT,
    FPS,
    GROUND_HEIGHT,
    GROUND_Y,
    PLAYER_SPEED,
    GRAVITY,
    BOMB_FUSE_MS,
    BOMB_RADIUS,
    BOMB_FORCE,
    BOMB_LIMIT,
    SHARD_SPEED,
    SHARD_LIFETIME,
    BOMB_COOLDOWN_MS,
    ENEMY_SPAWN_MS,
    MAX_ENEMIES,
    SAVE_FILE,
)
from game.utils import clamp
from game.entities import Player, Bomb, Shard, Enemy, ExplosionEffect
from game import rendering

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


def save_game(filename, player, bombs, shards, enemies, score, high_score, lives, last_spawn):
    state = {
        "player": {
            "x": player.x,
            "y": player.y,
            "vx": player.vx,
            "vy": player.vy,
            "on_ground": player.on_ground,
            "bombs_left": player.bombs_left,
            "pending_bomb": player.pending_bomb,
            "bomb_cooldown": player.bomb_cooldown,
        },
        "bombs": [
            {
                "x": bomb.x,
                "y": bomb.y,
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


def run_game():
    # Menu / game state
    menu_options = ["Start Game", "Load Game", "Quit"]
    selected = 0

    # game variables (initialized when starting)
    player = None
    bombs = []
    shards = []
    enemies = []
    effects = []
    score = 0
    high_score = 0
    lives = 3
    running = True
    game_over = False
    last_spawn = pygame.time.get_ticks()
    state = "menu"

    def start_new_game():
        nonlocal player, bombs, shards, enemies, effects, score, lives, game_over, last_spawn
        player = Player()
        bombs = []
        shards = []
        enemies = []
        effects = []
        score = 0
        lives = 3
        game_over = False
        last_spawn = pygame.time.get_ticks()

    while running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if state == "menu":
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(menu_options)
                    if event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(menu_options)
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = menu_options[selected]
                        if choice == "Start Game":
                            start_new_game()
                            state = "playing"
                        elif choice == "Load Game":
                            loaded = load_game(SAVE_FILE)
                            if loaded:
                                player = Player()
                                player.x = loaded["player"]["x"]
                                player.y = loaded["player"]["y"]
                                player.vx = loaded["player"]["vx"]
                                player.vy = loaded["player"]["vy"]
                                player.on_ground = loaded["player"]["on_ground"]
                                player.bombs_left = loaded["player"]["bombs_left"]
                                player.pending_bomb = loaded["player"]["pending_bomb"]
                                player.bomb_cooldown = loaded["player"].get("bomb_cooldown", 0)
                                player.rect.topleft = (player.x, player.y)
                                bombs = [Bomb.from_dict(b) for b in loaded["bombs"]]
                                shards = [Shard.from_dict(s) for s in loaded["shards"]]
                                enemies = [Enemy.from_dict(e) for e in loaded["enemies"]]
                                score = loaded.get("score", 0)
                                high_score = loaded.get("high_score", 0)
                                lives = loaded.get("lives", 3)
                                last_spawn = loaded.get("last_spawn", pygame.time.get_ticks())
                                effects = []
                                state = "playing"
                        elif choice == "Quit":
                            running = False
                else:
                    # in-game key handling
                    if event.key == pygame.K_SPACE:
                        if not game_over:
                            player.jump()
                        else:
                            start_new_game()
                            state = "playing"
                    if event.key == pygame.K_r and game_over:
                        start_new_game()
                        state = "playing"
                    if event.key == pygame.K_s:
                        save_game(SAVE_FILE, player, bombs, shards, enemies, score, high_score, lives, last_spawn)
                    if event.key == pygame.K_l:
                        loaded = load_game(SAVE_FILE)
                        if loaded:
                            player.x = loaded["player"]["x"]
                            player.y = loaded["player"]["y"]
                            player.vx = loaded["player"]["vx"]
                            player.vy = loaded["player"]["vy"]
                            player.on_ground = loaded["player"]["on_ground"]
                            player.bombs_left = loaded["player"]["bombs_left"]
                            player.pending_bomb = loaded["player"]["pending_bomb"]
                            player.bomb_cooldown = loaded["player"].get("bomb_cooldown", 0)
                            player.rect.topleft = (player.x, player.y)
                            bombs = [Bomb.from_dict(b) for b in loaded["bombs"]]
                            shards = [Shard.from_dict(s) for s in loaded["shards"]]
                            enemies = [Enemy.from_dict(e) for e in loaded["enemies"]]
                            score = loaded.get("score", score)
                            high_score = loaded.get("high_score", high_score)
                            lives = loaded.get("lives", lives)
                            last_spawn = loaded.get("last_spawn", last_spawn)
                    if event.key == pygame.K_ESCAPE:
                        # Return to the main menu instead of quitting
                        state = "menu"

        screen.fill((18, 30, 50))

        # simple parallax background using player X as camera when playing
        cam_x = int(player.x - WIDTH // 2) if (player and state == "playing") else 0
        rendering.draw_parallax_background(screen, cam_x)

        if state == "menu":
            rendering.draw_menu(screen, font, small_font, menu_options, selected)

        elif state == "playing":
            # main game loop body
            if not game_over:
                spawn_bomb = player.update(keys, dt)
                now = pygame.time.get_ticks()

                if spawn_bomb:
                    bombs.append(player.create_bomb())

                if len(enemies) < MAX_ENEMIES and now - last_spawn >= ENEMY_SPAWN_MS:
                    side = random.choice(["left", "right"])
                    enemies.append(Enemy(side))
                    last_spawn = now

                for bomb in bombs[:]:
                    bomb.update(dt)
                    # explode if fuse ready OR if any enemy touches the bomb
                    triggered = False
                    if bomb.is_ready():
                        triggered = True
                    else:
                        for e in enemies:
                            if bomb.rect.colliderect(e.rect):
                                triggered = True
                                break

                    if triggered:
                        effects.append(ExplosionEffect(bomb.x, bomb.y, bomb.radius))
                        player.apply_explosion(bomb.x, bomb.y, bomb.radius)
                        for enemy in enemies:
                            if enemy.killed_by_explosion(bomb.x, bomb.y, bomb.radius):
                                enemy.take_damage()
                        if bomb.has_shrapnel:
                            shards.extend(Shard(bomb.x, bomb.y, angle, SHARD_SPEED * 1.25) for angle in [i * math.pi * 2 / 10 for i in range(10)])
                        if bomb in bombs:
                            bombs.remove(bomb)
                        player.bombs_left = min(player.bombs_left + 1, BOMB_LIMIT)

                for enemy in enemies[:]:
                    enemy.update(dt)
                    if not enemy.dead:
                        for shard in shards[:]:
                            if shard.rect.colliderect(enemy.rect):
                                enemy.take_damage()
                                if shard in shards:
                                    shards.remove(shard)
                                break

                    if enemy.dead:
                        shards.extend(enemy.get_death_shrapnel())
                        score += 100
                        enemies.remove(enemy)
                    elif enemy.rect.colliderect(player.rect):
                        lives -= 1
                        if lives <= 0:
                            game_over = True
                            high_score = max(high_score, score)
                        else:
                            start_new_game()
                            state = "playing"
                            break

                for shard in shards[:]:
                    shard.update(dt)
                    if shard.rect.colliderect(player.rect):
                        lives -= 1
                        if lives <= 0:
                            game_over = True
                            high_score = max(high_score, score)
                            break
                        else:
                            start_new_game()
                            state = "playing"
                            break
                    if not shard.is_alive():
                        shards.remove(shard)

                for effect in effects[:]:
                    effect.update(dt)
                    if not effect.is_alive():
                        effects.remove(effect)

                score += 1

            rendering.draw_ground(screen)
            rendering.draw_scene(screen, player, bombs, shards, enemies, effects)
            rendering.draw_hud(screen, font, small_font, score, high_score, player.bombs_left, lives, player.bomb_cooldown)

            if game_over:
                rendering.draw_game_over_overlay(screen, font, small_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
