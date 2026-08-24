import sys
import pygame

from game.config import WIDTH, HEIGHT, FPS, DEBUG_ENV_VAR
from game.rendering import renderer as rendering
from game.input import key_mapping as game_input
from game.scene.game_app import GameApp
from game.utils import env_flag

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


def run_game():
    app = GameApp(debug=env_flag(DEBUG_ENV_VAR))

    while app.running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.running = False
            if event.type == pygame.KEYDOWN:
                action = game_input.map_key(app.state, event.key)
                if action:
                    app.handle_action(action, now)

        screen.fill((18, 30, 50))

        # simple parallax background using player X as camera when playing
        cam_x = int(app.world.player.x - WIDTH // 2) if (app.world and app.state == "playing") else 0
        rendering.draw_parallax_background(screen, cam_x)

        if app.state == "menu":
            rendering.draw_menu(screen, font, small_font, app.menu_options, app.selected)

        elif app.state == "playing":
            app.tick(keys, dt, now)
            world = app.world

            rendering.draw_ground(screen)
            rendering.draw_scene(screen, world.player, world.bombs, world.shards, world.enemies, world.effects)
            if app.debug:
                rendering.draw_debug_boxes(screen, world.player, world.bombs, world.shards, world.enemies)
            rendering.draw_hud(screen, font, small_font, world.score, app.high_score, world.player.bombs_left, world.lives, world.player.bomb_cooldown)

            if world.game_over:
                rendering.draw_game_over_overlay(screen, font, small_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
