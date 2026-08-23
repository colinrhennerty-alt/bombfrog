import sys
import pygame

from game.config import WIDTH, HEIGHT, FPS, SAVE_FILE
from game import rendering
from game.persistence import save_game, load_game
from game.world import World

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


def run_game():
    # Menu / game state
    menu_options = ["Start Game", "Load Game", "Quit"]
    selected = 0

    world = None
    high_score = 0
    running = True
    state = "menu"

    while running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

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
                            world = World(now)
                            state = "playing"
                        elif choice == "Load Game":
                            loaded = load_game(SAVE_FILE)
                            if loaded:
                                world = World.from_save_data(loaded, now)
                                high_score = loaded.get("high_score", 0)
                                state = "playing"
                        elif choice == "Quit":
                            running = False
                else:
                    # in-game key handling
                    if event.key == pygame.K_SPACE:
                        if not world.game_over:
                            world.player.jump()
                        else:
                            world.reset(now)
                            state = "playing"
                    if event.key == pygame.K_r and world.game_over:
                        world.reset(now)
                        state = "playing"
                    if event.key == pygame.K_s:
                        save_game(
                            SAVE_FILE, world.player, world.bombs, world.shards, world.enemies,
                            world.score, high_score, world.lives, world.last_spawn,
                        )
                    if event.key == pygame.K_l:
                        loaded = load_game(SAVE_FILE)
                        if loaded:
                            world.merge_save_data(loaded)
                            high_score = loaded.get("high_score", high_score)
                    if event.key == pygame.K_ESCAPE:
                        # Return to the main menu instead of quitting
                        state = "menu"

        screen.fill((18, 30, 50))

        # simple parallax background using player X as camera when playing
        cam_x = int(world.player.x - WIDTH // 2) if (world and state == "playing") else 0
        rendering.draw_parallax_background(screen, cam_x)

        if state == "menu":
            rendering.draw_menu(screen, font, small_font, menu_options, selected)

        elif state == "playing":
            world.update(keys, dt, now)
            if world.game_over:
                high_score = max(high_score, world.score)

            rendering.draw_ground(screen)
            rendering.draw_scene(screen, world.player, world.bombs, world.shards, world.enemies, world.effects)
            rendering.draw_hud(screen, font, small_font, world.score, high_score, world.player.bombs_left, world.lives, world.player.bomb_cooldown)

            if world.game_over:
                rendering.draw_game_over_overlay(screen, font, small_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
