from game.paths import user_data_path

WIDTH = 1700
HEIGHT = 900
FPS = 60
WORLD_WIDTH = WIDTH * 4
WORLD_HEIGHT = HEIGHT * 4
WORLD_BORDER = 180
# Every entity (and the sprite drawn into its hitbox) is its base pixel
# size times ENTITY_SCALE — one knob to grow/shrink all characters at once.
ENTITY_SCALE = 2
# The frog's grounded body: its cropped art is 18 px wide and ~13 px tall
# when sitting, at 1.5 base px per art px.
PLAYER_BASE_SIZE = (27, 20)
PLAYER_SIZE = (PLAYER_BASE_SIZE[0] * ENTITY_SCALE, PLAYER_BASE_SIZE[1] * ENTITY_SCALE)
# Enemies have no base size of their own — each EnemyType is sized relative
# to the frog (height_vs_frog), so they follow ENTITY_SCALE through PLAYER_SIZE.
SHARD_BASE_RADIUS = 4
FROG_ANIM_MS = 220
ENEMY_ANIM_MS = 100
FROG_IDLE_FRAME_COUNT = 6
PLAYER_SPEED = 5
GRAVITY = 0.8
BOMB_FUSE_MS = 900
BOMB_RADIUS = 140
BOMB_FORCE = 24
BOMB_LIMIT = 2
BOMB_CONTACT_GRACE_MS = 180
SHARD_SPEED = 8
SHARD_LIFETIME = 1500
BOMB_COOLDOWN_MS = 1200
BOMB_FALL_SPEED = 40
ENEMY_SPAWN_MS = 1800
MAX_ENEMIES = 5
SAVE_FILE = user_data_path("savegame.json")
LEVEL_FILE = user_data_path("levels/level.json")
EDITOR_SIDEBAR_WIDTH = 220
DEBUG_ENV_VAR = "BOMBFROG_DEBUG"
