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

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


def world_scale(y, obj_h=0):
    # returns a simple scale factor based on vertical position (0..GROUND_Y)
    denom = max(1, GROUND_Y - obj_h)
    t = clamp(y / denom, 0.0, 1.0)
    return 0.8 + 0.4 * t


def draw_shadow(surface, x, y, base_radius, scale):
    # Draw a simple blurred shadow projected onto the ground
    # shadow position anchored near ground under object
    sx = int(x)
    sy = GROUND_Y - int(6 * scale)
    sr = max(6, int(base_radius * scale * 0.6))
    shadow = pygame.Surface((sr * 2, int(sr * 0.6)), pygame.SRCALPHA)
    alpha = int(120 * clamp(1.0 - (y / float(GROUND_Y)), 0.3, 1.0))
    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, 0, sr * 2, int(sr * 0.6)))
    surface.blit(shadow, (sx - sr, sy - int(sr * 0.3)))


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


def draw_hud(surface, score, high_score, bombs_left, lives, bomb_cooldown):
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    high_text = small_font.render(f"High Score: {high_score}", True, (240, 240, 240))
    bomb_text = small_font.render(f"Bombs: {bombs_left}", True, (255, 220, 120))
    life_text = small_font.render(f"Lives: {lives}", True, (180, 210, 255))
    legend_title = small_font.render("Enemies:", True, (220, 220, 220))
    grunt_text = small_font.render("Grunt", True, (190, 80, 80))
    heavy_text = small_font.render("Heavy", True, (170, 130, 80))
    elite_text = small_font.render("Elite", True, (150, 95, 185))
    prompt_text = small_font.render("SPACE = jump/save bomb | S=save | L=load | avoid shards", True, (210, 210, 210))
    surface.blit(score_text, (20, 20))
    surface.blit(high_text, (20, 60))
    surface.blit(bomb_text, (20, 100))
    cooldown_text = small_font.render(f"Bomb CD: {max(0, int(bomb_cooldown / 1000 * 10) / 10):.1f}s", True, (255, 200, 120))
    surface.blit(life_text, (20, 140))
    surface.blit(cooldown_text, (20, 170))
    surface.blit(legend_title, (20, 210))
    pygame.draw.circle(surface, (190, 80, 80), (30, 210), 5)
    surface.blit(grunt_text, (45, 204))
    pygame.draw.circle(surface, (170, 130, 80), (30, 232), 5)
    surface.blit(heavy_text, (45, 226))
    pygame.draw.circle(surface, (150, 95, 185), (30, 254), 5)
    surface.blit(elite_text, (45, 248))
    surface.blit(prompt_text, (20, HEIGHT - 40))


def draw_ground(surface):
    pygame.draw.rect(surface, (90, 54, 20), (0, GROUND_Y, WIDTH, GROUND_HEIGHT))
    for i in range(0, WIDTH, 80):
        pygame.draw.arc(surface, (77, 45, 16), (i, GROUND_Y - 40, 80, 80), math.pi, 0, 4)


def draw_overlay(surface, bombs):
    for bomb in bombs:
        if bomb.timer > 0:
            radius = int(bomb.radius * (1 - bomb.timer / BOMB_FUSE_MS) * 0.5 + 20)
            pygame.draw.circle(surface, (255, 170, 0, 40), (int(bomb.x), int(bomb.y)), radius, 1)


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
        # far sky / mountains
        pygame.draw.rect(screen, (18, 30, 50), (0, 0, WIDTH, HEIGHT))
        m1_x = -int(cam_x * 0.12) % (WIDTH * 2)
        pygame.draw.ellipse(screen, (50, 60, 90), (m1_x - 300, 40, WIDTH + 600, 180))
        pygame.draw.ellipse(screen, (60, 70, 110), (m1_x + 200, 100, WIDTH, 140))
        # near hills
        m2_x = -int(cam_x * 0.24) % (WIDTH * 2)
        pygame.draw.ellipse(screen, (70, 50, 30), (m2_x - 200, GROUND_Y - 80, WIDTH + 400, 160))

        if state == "menu":
            # draw title and menu
            title = font.render("Bomb Frog", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
            subtitle = small_font.render("Leapfrog with bombs — press Enter to select", True, (220, 220, 220))
            screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 130))

            for i, opt in enumerate(menu_options):
                color = (255, 220, 120) if i == selected else (200, 200, 200)
                text = font.render(opt, True, color)
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 220 + i * 60))

            hint = small_font.render("Use UP/DOWN to move, ENTER to confirm", True, (180, 180, 180))
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))

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

            draw_ground(screen)

            # depth-sorted drawing: shadows first, then sprites
            drawables = []
            drawables.extend(enemies)
            drawables.extend(bombs)
            drawables.extend(shards)
            if player:
                drawables.append(player)

            def depth_key(o):
                if hasattr(o, "y"):
                    return o.y
                if hasattr(o, "rect"):
                    return o.rect.bottom
                return 0

            drawables = sorted(drawables, key=depth_key)

            # draw shadows
            for o in drawables:
                ox = getattr(o, "x", getattr(o, "rect", pygame.Rect(0, 0, 0, 0)).centerx)
                oy = getattr(o, "y", getattr(o, "rect", pygame.Rect(0, 0, 0, 0)).centery)
                base_r = getattr(o, "radius", getattr(o, "width", 20))
                scale = world_scale(oy, getattr(o, "height", 0))
                draw_shadow(screen, ox, oy, base_r, scale)

            # draw sprites in depth order
            for o in drawables:
                try:
                    o.draw(screen)
                except Exception:
                    pass

            # draw effects on top
            for effect in effects:
                effect.draw(screen)

            draw_hud(screen, score, high_score, player.bombs_left, lives, player.bomb_cooldown)

            if game_over:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                game_over_text = font.render("Game Over", True, (255, 220, 90))
                restart_text = small_font.render("Press SPACE or R to restart, ESC to quit.", True, (245, 245, 245))
                screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
                screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
