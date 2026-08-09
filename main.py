import random
import sys
import pygame

# Game settings
WIDTH = 800
HEIGHT = 600
FPS = 60
GROUND_HEIGHT = 80
PLAYER_SPEED = 6
JUMP_POWER = 16
GRAVITY = 0.6
BOMB_RADIUS = 2
BOMB_SPEED_MIN = 1
BOMB_SPEED_MAX = 2
SPAWN_INTERVAL_MS = 1200000

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


class Player:
    def __init__(self):
        self.width = 60
        self.height = 40
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - GROUND_HEIGHT - self.height
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.color = (43, 175, 76)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED

        self.x += self.vx
        self.x = max(0, min(WIDTH - self.width, self.x))

        if not self.on_ground:
            self.vy += GRAVITY
            self.y += self.vy
            if self.y >= HEIGHT - GROUND_HEIGHT - self.height:
                self.y = HEIGHT - GROUND_HEIGHT - self.height
                self.vy = 0
                self.on_ground = True

        self.rect.topleft = (self.x, self.y)

    def jump(self):
        if self.on_ground:
            self.vy = -JUMP_POWER
            self.on_ground = False

    def draw(self, surface):
        pygame.draw.ellipse(surface, self.color, self.rect)
        eye = pygame.Rect(self.x + self.width * 0.6, self.y + 10, 10, 10)
        pygame.draw.ellipse(surface, (255, 255, 255), eye)
        pygame.draw.ellipse(surface, (0, 0, 0), eye.inflate(-6, -6))


class Bomb:
    def __init__(self):
        self.radius = BOMB_RADIUS
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = -self.radius * 2
        self.vy = random.uniform(BOMB_SPEED_MIN, BOMB_SPEED_MAX)
        self.vx = random.uniform(-1.5, 1.5)
        self.color = (180, 40, 40)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < self.radius or self.x > WIDTH - self.radius:
            self.vx *= -1
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        fuse_start = (int(self.x), int(self.y - self.radius))
        fuse_end = (int(self.x), int(self.y - self.radius - 20))
        pygame.draw.line(surface, (230, 230, 100), fuse_start, fuse_end, 4)
        pygame.draw.circle(surface, (255, 255, 150), fuse_end, 6)

    def is_offscreen(self):
        return self.y - self.radius > HEIGHT


def draw_hud(surface, score, high_score):
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    high_text = small_font.render(f"High Score: {high_score}", True, (240, 240, 240))
    surface.blit(score_text, (20, 20))
    surface.blit(high_text, (20, 60))


def draw_ground(surface):
    pygame.draw.rect(surface, (90, 54, 20), (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))
    for i in range(0, WIDTH, 80):
        pygame.draw.arc(surface, (77, 45, 16), (i, HEIGHT - GROUND_HEIGHT - 40, 80, 80), 3.14, 0, 4)


def draw_title(surface):
    title = font.render("Bomb Frog", True, (255, 255, 255))
    sub = small_font.render("Avoid the bombs and survive as long as possible.", True, (220, 220, 220))
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
    surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 210))


def run_game():
    player = Player()
    bombs = []
    score = 0
    high_score = 0
    running = True
    game_over = False
    last_spawn = pygame.time.get_ticks()

    while running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    if not game_over:
                        player.jump()
                    elif game_over:
                        player = Player()
                        bombs = []
                        score = 0
                        game_over = False
                        last_spawn = pygame.time.get_ticks()
                if event.key == pygame.K_r and game_over:
                    player = Player()
                    bombs = []
                    score = 0
                    game_over = False
                    last_spawn = pygame.time.get_ticks()
                if event.key == pygame.K_ESCAPE:
                    running = False

        if not game_over:
            player.update(keys)
            now = pygame.time.get_ticks()
            if now - last_spawn >= max(300, SPAWN_INTERVAL_MS - score * 10):
                bombs.append(Bomb())
                last_spawn = now

            for bomb in bombs:
                bomb.update()

            bombs = [bomb for bomb in bombs if not bomb.is_offscreen()]

            for bomb in bombs:
                if player.rect.colliderect(bomb.rect):
                    game_over = True
                    high_score = max(high_score, score)
                    break

            score += 1

        screen.fill((28, 63, 110))
        draw_ground(screen)
        player.draw(screen)
        for bomb in bombs:
            bomb.draw(screen)

        draw_hud(screen, score, high_score)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            game_over_text = font.render("Game Over", True, (255, 200, 50))
            restart_text = small_font.render("Press SPACE or R to restart, ESC to quit.", True, (245, 245, 245))
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
