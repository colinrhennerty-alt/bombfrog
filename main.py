import sys
import pygame

from game.config import WIDTH, HEIGHT, FPS, DEBUG_ENV_VAR, GAMEPAD_STICK_DEADZONE
from game.rendering import renderer as rendering
from game.input import key_mapping as game_input
from game.input import gamepad_mapping
from game.input.gamepad_mapping import axis_to_digital
from game.scene.game_app import GameApp
from game.utils import env_flag

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()


class MergedKeys:
    """A pygame.key.get_pressed()-like object that also reports a
    connected gamepad's left stick / d-pad as digital arrow-key state,
    so Player/World never need to know a controller exists."""

    def __init__(self, keys, joystick):
        self._keys = keys
        self._left = self._right = self._up = self._down = False
        if joystick is not None:
            x = axis_to_digital(joystick.get_axis(0), GAMEPAD_STICK_DEADZONE)
            y = axis_to_digital(joystick.get_axis(1), GAMEPAD_STICK_DEADZONE)
            hat_x, hat_y = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)
            self._left = x == -1 or hat_x == -1
            self._right = x == 1 or hat_x == 1
            self._up = y == -1 or hat_y == 1
            self._down = y == 1 or hat_y == -1

    def __getitem__(self, key):
        if key == pygame.K_LEFT:
            return self._keys[key] or self._left
        if key == pygame.K_RIGHT:
            return self._keys[key] or self._right
        if key == pygame.K_UP:
            return self._keys[key] or self._up
        if key == pygame.K_DOWN:
            return self._keys[key] or self._down
        return self._keys[key]


def run_game():
    app = GameApp(debug=env_flag(DEBUG_ENV_VAR))

    while app.running:
        dt = clock.tick(FPS)
        keys = MergedKeys(pygame.key.get_pressed(), joystick)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.running = False
            if event.type == pygame.KEYDOWN:
                action = game_input.map_key(app.state, event.key)
                if action:
                    app.handle_action(action, now)
            if event.type == pygame.JOYBUTTONDOWN:
                action = gamepad_mapping.map_button(app.state, event.button)
                if action:
                    app.handle_action(action, now)
            if event.type == pygame.JOYHATMOTION:
                action = gamepad_mapping.map_hat(app.state, event.value)
                if action:
                    app.handle_action(action, now)
            if app.state == "editor":
                editor = app.editor_state
                if event.type == pygame.MOUSEMOTION:
                    if not editor.point_is_in_sidebar(*event.pos):
                        editor.set_hover(*event.pos)
                    if editor.is_dragging and not editor.point_is_in_sidebar(*event.pos):
                        editor.paint_at_screen(*event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if editor.point_is_in_sidebar(*event.pos):
                        result = editor.handle_sidebar_click(*event.pos)
                        if result == "save":
                            editor.save(app.level_file)
                        elif result == "load":
                            editor.load(app.level_file)
                    else:
                        editor.is_dragging = True
                        editor.paint_at_screen(*event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    editor.is_dragging = False

        screen.fill((18, 30, 50))

        if app.state == "menu":
            rendering.draw_menu(screen, font, small_font, app.menu_options, app.selected)

        elif app.state == "editor":
            rendering.draw_editor(screen, app.editor_state)
            rendering.draw_editor_sidebar(screen, app.editor_state, small_font)

        elif app.state == "playing":
            app.tick(keys, dt, now)
            world = app.world

            rendering.draw_ground(screen, world.camera)
            rendering.draw_scene(screen, world.player, world.bombs, world.shards, world.enemies, world.effects, world.camera)
            if app.debug:
                rendering.draw_debug_boxes(screen, world.player, world.bombs, world.shards, world.enemies, world.camera)
            rendering.draw_hud(screen, font, small_font, world.score, app.high_score, world.player.bombs_left, world.lives, world.player.bomb_cooldown)

            if world.game_over:
                rendering.draw_game_over_overlay(screen, font, small_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
