import math
import random
import sys
import pygame

# Game settings
WIDTH = 900
HEIGHT = 600
FPS = 60
GROUND_HEIGHT = 80
GROUND_Y = HEIGHT - GROUND_HEIGHT
PLAYER_SPEED = 5
GRAVITY = 0.8
BOMB_FUSE_MS = 900
BOMB_RADIUS = 100
BOMB_FORCE = 24
BOMB_LIMIT = 2
SHARD_SPEED = 8
SHARD_LIFETIME = 1500
ENEMY_SPAWN_MS = 1800
MAX_ENEMIES = 5

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomb Frog")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


class Player:
    def __init__(self):
        self.width = 52
        self.height = 40
        self.x = WIDTH // 2 - self.width // 2
        self.y = GROUND_Y - self.height
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.bombs_left = BOMB_LIMIT
        self.pending_bomb = False
        self.color = (43, 175, 76)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    @property
    def centerx(self):
        return self.x + self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2

    def update(self, keys, dt):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED

        self.x += self.vx
        self.x = clamp(self.x, 0, WIDTH - self.width)

        old_vy = self.vy
        if not self.on_ground:
            self.vy += GRAVITY

        self.y += self.vy
        spawn_bomb = False
        if self.pending_bomb and old_vy < 0 and self.vy >= 0:
            self.pending_bomb = False
            spawn_bomb = True

        if self.y >= GROUND_Y - self.height:
            self.y = GROUND_Y - self.height
            self.vy = 0
            self.on_ground = True
            self.pending_bomb = False

        self.rect.topleft = (self.x, self.y)
        return spawn_bomb

    def jump(self):
        if self.on_ground:
            self.vy = -GRAVITY * 24
            self.on_ground = False
            if self.bombs_left > 0:
                self.pending_bomb = True
                self.bombs_left -= 1

    def create_bomb(self):
        bomb_x = self.centerx
        bomb_y = GROUND_Y - 16
        return Bomb(bomb_x, bomb_y)

    def apply_explosion(self, origin_x, origin_y, radius):
        dx = self.centerx - origin_x
        dy = self.centery - origin_y
        dist = math.hypot(dx, dy)
        if dist >= radius:
            return

        strength = (radius - dist) / radius
        push_x = dx / dist if dist else 0
        self.vx += push_x * BOMB_FORCE * strength
        upward = -BOMB_FORCE * 0.7 * strength
        if self.vy > upward:
            self.vy = upward
        self.on_ground = False

    def draw(self, surface):
        body = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.ellipse(surface, self.color, body)
        eye = pygame.Rect(self.x + self.width * 0.55, self.y + 10, 10, 10)
        pygame.draw.ellipse(surface, (255, 255, 255), eye)
        pygame.draw.ellipse(surface, (0, 0, 0), eye.inflate(-6, -6))
        bomb_icon = pygame.Rect(self.x + 8, self.y + self.height - 16, 12, 12)
        pygame.draw.circle(surface, (200, 200, 50), bomb_icon.center, 6)


class Bomb:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = BOMB_RADIUS
        self.timer = BOMB_FUSE_MS
        self.color = (210, 70, 70)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self, dt):
        self.timer -= dt
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 14)
        fuse_ratio = max(0, self.timer / BOMB_FUSE_MS)
        pygame.draw.arc(
            surface,
            (255, 240, 120),
            (self.x - 20, self.y - 20, 40, 40),
            math.pi * 0.5,
            math.pi * 0.5 + math.pi * 2 * fuse_ratio,
            4,
        )

    def is_ready(self):
        return self.timer <= 0

    def draw_explosion_radius(self, surface):
        pygame.draw.circle(surface, (255, 180, 0, 40), (int(self.x), int(self.y)), self.radius, 2)


class Shard:
    def __init__(self, x, y, angle, speed, color=None):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = SHARD_LIFETIME
        self.radius = 4
        self.color = color or (255, 220, 100)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self, dt):
        self.vy += GRAVITY * 0.2
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        self.rect.topleft = (self.x - self.radius, self.y - self.radius)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def is_alive(self):
        return self.life > 0 and 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT


class Enemy:
    def __init__(self, spawn_side):
        self.width = 40
        self.height = 34
        self.type = random.choices(["grunt", "heavy", "elite"], [0.55, 0.30, 0.15])[0]
        if spawn_side == "left":
            self.x = -self.width - 20
            self.vx = 2.2
        else:
            self.x = WIDTH + 20
            self.vx = -2.2
        self.y = GROUND_Y - self.height
        self.color = {
            "grunt": (190, 80, 80),
            "heavy": (170, 130, 80),
            "elite": (150, 95, 185),
        }[self.type]
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.dead = False

    def update(self, dt):
        self.x += self.vx
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        if self.type == "elite":
            pygame.draw.circle(surface, (255, 255, 255), self.rect.center, 6)

    def killed_by_explosion(self, origin_x, origin_y, radius):
        dx = self.rect.centerx - origin_x
        dy = self.rect.centery - origin_y
        return math.hypot(dx, dy) < radius * 0.75

    def get_death_shrapnel(self):
        center_x = self.rect.centerx
        center_y = self.rect.centery
        shards = []
        if self.type == "grunt":
            for i in range(6):
                angle = math.pi * 2 * i / 6
                shards.append(Shard(center_x, center_y, angle, SHARD_SPEED * 1.1))
        elif self.type == "heavy":
            direction = 0 if self.vx > 0 else math.pi
            for i in range(-2, 3):
                angle = direction + i * 0.3
                shards.append(Shard(center_x, center_y, angle, SHARD_SPEED * 1.3, (220, 140, 80)))
        else:  # elite
            for i in range(8):
                angle = math.pi * 2 * i / 8
                shards.append(Shard(center_x, center_y, angle, SHARD_SPEED * 0.9, (200, 140, 240)))
        return shards


class ExplosionEffect:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.life = 260

    def update(self, dt):
        self.life -= dt

    def draw(self, surface):
        alpha = int(180 * max(0, self.life / 260))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (255, 180, 60, alpha), (int(self.x), int(self.y)), int(self.radius), 4)
        surface.blit(overlay, (0, 0))

    def is_alive(self):
        return self.life > 0


def draw_hud(surface, score, high_score, bombs_left):
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    high_text = small_font.render(f"High Score: {high_score}", True, (240, 240, 240))
    bomb_text = small_font.render(f"Bombs: {bombs_left}", True, (255, 220, 120))
    prompt_text = small_font.render("SPACE = place bomb | avoid shards and enemies", True, (210, 210, 210))
    surface.blit(score_text, (20, 20))
    surface.blit(high_text, (20, 60))
    surface.blit(bomb_text, (20, 100))
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
    player = Player()
    bombs = []
    shards = []
    enemies = []
    effects = []
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
                if event.key == pygame.K_SPACE:
                    if not game_over:
                        player.jump()
                    else:
                        player = Player()
                        bombs = []
                        shards = []
                        enemies = []
                        effects = []
                        score = 0
                        game_over = False
                        last_spawn = pygame.time.get_ticks()
                if event.key == pygame.K_r and game_over:
                    player = Player()
                    bombs = []
                    shards = []
                    enemies = []
                    effects = []
                    score = 0
                    game_over = False
                    last_spawn = pygame.time.get_ticks()
                if event.key == pygame.K_ESCAPE:
                    running = False

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
                if bomb.is_ready():
                    effects.append(ExplosionEffect(bomb.x, bomb.y, bomb.radius))
                    player.apply_explosion(bomb.x, bomb.y, bomb.radius)
                    for enemy in enemies:
                        if enemy.killed_by_explosion(bomb.x, bomb.y, bomb.radius):
                            enemy.dead = True
                    shards.extend(Shard(bomb.x, bomb.y, angle, SHARD_SPEED * 1.25) for angle in [i * math.pi * 2 / 10 for i in range(10)])
                    bombs.remove(bomb)
                    player.bombs_left = min(player.bombs_left + 1, BOMB_LIMIT)

            for enemy in enemies[:]:
                enemy.update(dt)
                if enemy.dead:
                    shards.extend(enemy.get_death_shrapnel())
                    score += 100
                    enemies.remove(enemy)
                elif enemy.rect.colliderect(player.rect):
                    game_over = True
                    high_score = max(high_score, score)

            for shard in shards[:]:
                shard.update(dt)
                if shard.rect.colliderect(player.rect):
                    game_over = True
                    high_score = max(high_score, score)
                    break
                if not shard.is_alive():
                    shards.remove(shard)

            for effect in effects[:]:
                effect.update(dt)
                if not effect.is_alive():
                    effects.remove(effect)

            score += 1

        screen.fill((26, 42, 78))
        draw_ground(screen)
        player.draw(screen)
        for bomb in bombs:
            bomb.draw(screen)
        for shard in shards:
            shard.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for effect in effects:
            effect.draw(screen)

        draw_hud(screen, score, high_score, player.bombs_left)

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
