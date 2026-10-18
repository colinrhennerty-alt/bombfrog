"""Every tuning constant: screen/world size, entity sizes, physics,
timings, and file locations. Times are in milliseconds; speeds are
pixels per frame (the game runs at a fixed FPS).
"""

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
# The bomb itself (not its blast — that's BOMB_RADIUS); reads slightly
# smaller than the frog (tests/test_visual_size.py).
BOMB_BODY_BASE_RADIUS = 9.5
FROG_ANIM_MS = 220
ENEMY_ANIM_MS = 100
FROG_IDLE_FRAME_COUNT = 6
PLAYER_SPEED = 5
GRAVITY = 0.8
BOMB_FUSE_MS = 900
BOMB_RADIUS = 140
BOMB_FORCE = 24
BOMB_LIMIT = 2
STARTING_LIVES = 3
BOMB_CONTACT_GRACE_MS = 180
SHARD_SPEED = 8
SHARD_LIFETIME = 1500
BOMB_COOLDOWN_MS = 1200
BOMB_FALL_SPEED = 40
ENEMY_SPAWN_MS = 1800
ENEMY_SPEED = 2.2
# Fraction of ENEMY_SPEED a multi-HP enemy has lost by its last HP (it
# limps more with each hit; one-HP enemies are never hurt, only dead).
ENEMY_INJURY_SLOWDOWN = 0.4
# Center-to-center distances. The first time the frog comes within
# ENEMY_NOTICE_RADIUS an enemy rolls its type's follow_chance once; a
# follower gives up past ENEMY_GIVE_UP_RADIUS (wider, so it doesn't flicker).
ENEMY_NOTICE_RADIUS = PLAYER_SIZE[0] * 5
ENEMY_GIVE_UP_RADIUS = ENEMY_NOTICE_RADIUS * 2.5
MAX_ENEMIES = 5
SAVE_FILE = user_data_path("savegame.json")
LEVEL_FILE = user_data_path("levels/level.json")
EDITOR_SIDEBAR_WIDTH = 220
DEBUG_ENV_VAR = "BOMBFROG_DEBUG"
