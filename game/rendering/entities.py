"""Drawing for everything that moves: the frog, bombs, shards, enemies and
explosion effects, plus their shadows and the debug hitbox overlay — and
the round's trees, which have to depth-sort in among them.

`draw_scene` is the entry point: it depth-sorts entities and trees by
where they touch the ground, draws shadows, then sprites, then effects.
"""

import math

import pygame

from game.config import HEIGHT, BOMB_FUSE_MS, ENTITY_SCALE
from game.utils import clamp
from game.simulation.player import Player
from game.simulation.bomb import Bomb
from game.simulation.shard import Shard
from game.simulation.enemy import Enemy
from game.simulation.enemy_types import ENEMY_TYPES
from game.simulation.trees import Tree
from game.simulation.obstacles import feet_rect
from game.rendering.assets import get_frog_frames, get_bomb_explosion_frames, get_bomb_sprite, get_critter_frames
from game.rendering.tree_assets import get_tree_sprite, get_tree_shadow

# Visual-only sizes for things whose rect isn't their drawn size (a bomb's
# rect is its blast area; an explosion has no rect). Base pixel sizes,
# multiplied by ENTITY_SCALE like every entity hitbox.
BOMB_SPRITE_BASE_MIN_SIZE = 16
# The fuse ring hugs the bomb body, so it's sized relative to it (and
# follows its depth scaling) rather than being a fixed size of its own.
FUSE_RING_RADIUS_VS_BODY = 1.4
FUSE_RING_WIDTH_VS_BODY = 0.28
EXPLOSION_SPRITE_BASE_MIN_SIZE = 24
# A hurt critter's colors blend toward ENEMY_INJURY_RED, by up to
# ENEMY_INJURY_TINT on its last HP (Enemy.injury == 1). Blending (rather
# than multiplying green/blue away) keeps dark art like the boar from just
# going black.
ENEMY_INJURY_RED = (220, 30, 30)
ENEMY_INJURY_TINT = 0.5
EXPLOSION_SPRITE_BASE_MAX_SIZE = 160


def shadow_size_for(base_radius, height_offset):
    """Shrink the shadow as the entity rises off the ground, so height
    reads visually even though the sim is pure 2D. height_offset is the
    same jump_offset/fall_offset magnitude used to draw the entity itself
    (0 = grounded, larger magnitude = higher up)."""
    shrink = 1 / (1 + abs(height_offset) / 60)
    return max(6, int(base_radius * 0.4 * shrink))


def draw_shadow(surface, x, y, base_radius, height_offset=0):
    # Draw a simple blurred shadow beneath the entity, in screen space
    # (caller has already applied the camera translation).
    sr = shadow_size_for(base_radius, height_offset)
    alpha = max(30, int(90 * (1 / (1 + abs(height_offset) / 60))))
    shadow = pygame.Surface((sr * 2, int(sr * 0.6)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, 0, sr * 2, int(sr * 0.6)))
    surface.blit(shadow, (int(x) - sr, int(y) - int(sr * 0.3)))


def draw_player(surface, player, camera):
    frames = get_frog_frames()
    if not player.on_ground:
        frame = frames["jump"]
    elif player.land_timer > 0:
        frame = frames["land"]
    else:
        frame = frames["idle"][player.anim_index]

    if player.facing > 0:
        frame = pygame.transform.flip(frame, True, False)

    # One uniform pixel scale, sized so the frame is as wide as the hitbox:
    # the frog is never stretched, and the hitbox covers its grounded body
    # while taller poses (the jump) extend upward past it. Feet go on the
    # hitbox's midbottom. Regular (not smooth) scale keeps pixel art crisp.
    width = player.rect.size[0]
    height = round(frame.get_height() * width / frame.get_width())
    frame = pygame.transform.scale(frame, (width, height))
    mid_x, bottom_y = camera.apply_rect(player.rect).midbottom
    surface.blit(frame, (mid_x - width // 2, bottom_y - height + int(player.jump_offset)))


def depth_scale_for(screen_y):
    """A cheap perspective-camera trick: entities nearer the top of the
    viewport read smaller, entities nearer the bottom read larger, as if
    the camera were looking down at an angle instead of straight down."""
    return 0.85 + 0.3 * clamp(screen_y / HEIGHT, 0, 1)


def bomb_body_radius(bomb, screen_y):
    return int(bomb.body_radius * depth_scale_for(screen_y))


def draw_bomb(surface, bomb, camera):
    sx, sy = camera.apply(bomb.x, bomb.y)
    sy += bomb.fall_offset
    r = bomb_body_radius(bomb, sy)
    pygame.draw.circle(surface, bomb.color, (int(sx), int(sy)), r)

    sprite = get_bomb_sprite()
    sprite_size = max(BOMB_SPRITE_BASE_MIN_SIZE * ENTITY_SCALE, int(r * 2.4))
    sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))
    sprite_rect = sprite.get_rect(center=(int(sx), int(sy)))
    surface.blit(sprite, sprite_rect)

    fuse_ratio = max(0, bomb.timer / BOMB_FUSE_MS)
    arc_r = int(r * FUSE_RING_RADIUS_VS_BODY)
    arc_rect = (sx - arc_r, sy - arc_r, arc_r * 2, arc_r * 2)
    pygame.draw.arc(
        surface, (255, 240, 120), arc_rect, math.pi * 0.5, math.pi * 0.5 + math.pi * 2 * fuse_ratio,
        max(1, int(r * FUSE_RING_WIDTH_VS_BODY)),
    )


def draw_bomb_explosion_radius(surface, bomb, camera):
    sx, sy = camera.apply(bomb.x, bomb.y)
    pygame.draw.circle(surface, (255, 180, 0, 40), (int(sx), int(sy)), bomb.radius, 2)


def draw_shard(surface, shard, camera):
    sx, sy = camera.apply(shard.x, shard.y)
    r = max(1, int(shard.radius * depth_scale_for(sy)))
    pygame.draw.circle(surface, shard.color, (int(sx), int(sy)), r)


_tint_cache = {}


def _tinted(frame, injury):
    """`frame` blended toward ENEMY_INJURY_RED by injury; alpha is untouched.
    Cached per (frame, injury) since critter frames are themselves cached."""
    key = (frame, round(injury, 2))
    if key not in _tint_cache:
        t = ENEMY_INJURY_TINT * injury
        keep = round(255 * (1 - t))
        tinted = frame.copy()
        tinted.fill((keep, keep, keep), special_flags=pygame.BLEND_RGB_MULT)
        tinted.fill(tuple(round(c * t) for c in ENEMY_INJURY_RED), special_flags=pygame.BLEND_RGB_ADD)
        _tint_cache[key] = tinted
    return _tint_cache[key]


def draw_enemy(surface, enemy, camera):
    # Enemies only move horizontally, so the sign of vx picks between the
    # critter's down-right (SE) and down-left (SW) isometric facings.
    facing = "SE" if enemy.vx > 0 else "SW"
    frames = get_critter_frames()[ENEMY_TYPES[enemy.type].sprite][facing]
    frame = frames[enemy.anim_index % len(frames)]
    if enemy.injury > 0:
        frame = _tinted(frame, enemy.injury)

    # Same contract as draw_player: scale into the collision rect itself so
    # the drawn sprite and the hitbox always match exactly.
    frame = pygame.transform.scale(frame, enemy.rect.size)
    surface.blit(frame, camera.apply_rect(enemy.rect).topleft)


def draw_explosion_effect(surface, effect, camera):
    sx, sy = camera.apply(effect.x, effect.y)
    frames = get_bomb_explosion_frames()
    frame_index = min(len(frames) - 1, max(0, int((260 - effect.life) / 260 * len(frames))))
    frame = frames[frame_index]
    sprite_size = max(
        EXPLOSION_SPRITE_BASE_MIN_SIZE * ENTITY_SCALE,
        min(EXPLOSION_SPRITE_BASE_MAX_SIZE * ENTITY_SCALE, int(effect.radius * 2.4 * ENTITY_SCALE)),
    )
    frame = pygame.transform.scale(frame, (sprite_size, sprite_size))
    rect = frame.get_rect(center=(int(sx), int(sy)))
    surface.blit(frame, rect)


_ENTITY_DRAW_SPECS = {
    Player: (draw_player, (0, 255, 0)),
    Bomb: (draw_bomb, (255, 80, 80)),
    Shard: (draw_shard, (255, 255, 0)),
    Enemy: (draw_enemy, (80, 160, 255)),
}


# Sprites whose art already has a shadow baked in; a generated ellipse on
# top of it doubles the shadow and makes the entity look like it hovers.
_ENTITIES_WITH_BAKED_SHADOWS = (Enemy,)


def _collect_entities(player, bombs, shards, enemies):
    """Every drawable entity for one frame, player last so it renders
    (and debug-outlines) on top of the cast around it."""
    entities = list(enemies) + list(bombs) + list(shards)
    if player:
        entities.append(player)
    return entities


DEBUG_TRUNK_COLOR = (150, 90, 40)
DEBUG_STUMP_COLOR = (230, 200, 60)  # jumpable
DEBUG_FEET_COLOR = (255, 255, 255)


def draw_debug_boxes(surface, player, bombs, shards, enemies, camera, obstacles=()):
    """Outlines the exact .rect each entity uses for colliderect checks
    in game.world — not an approximation, the real hitbox — plus the
    tree-trunk footprints and the feet strips that collide with them."""
    for entity in _collect_entities(player, bombs, shards, enemies):
        _, color = _ENTITY_DRAW_SPECS.get(type(entity), (None, (255, 255, 255)))
        pygame.draw.rect(surface, color, camera.apply_rect(entity.rect), width=2)
    for obstacle in obstacles:
        color = DEBUG_STUMP_COLOR if obstacle.jumpable else DEBUG_TRUNK_COLOR
        pygame.draw.rect(surface, color, camera.apply_rect(obstacle.rect), width=2)
    for mover in ([player] if player else []) + list(enemies):
        feet = feet_rect(mover.x, mover.y, mover.width, mover.height)
        pygame.draw.rect(surface, DEBUG_FEET_COLOR, camera.apply_rect(feet), width=1)


def _placed_rect(image_and_offset, tree, camera):
    image, (dx, dy) = image_and_offset
    sx, sy = camera.apply(tree.x, tree.y)
    return pygame.Rect(int(sx + dx), int(sy + dy), image.get_width(), image.get_height())


def tree_screen_rect(tree, camera):
    """Where a tree's sprite lands on screen, trunk base at tree.x/y."""
    return _placed_rect(get_tree_sprite(tree.kind), tree, camera)


def draw_tree_shadow(surface, tree, camera):
    shadow = get_tree_shadow(tree.kind)
    surface.blit(shadow[0], _placed_rect(shadow, tree, camera))


def draw_tree(surface, tree, camera, faded=False):
    sprite = get_tree_sprite(tree.kind, faded)
    surface.blit(sprite[0], _placed_rect(sprite, tree, camera))


def _ground_y(drawable):
    """Where a drawable touches the ground — the depth-sort key, so a tall
    tree and a short frog compare at their bases, not their tops."""
    return drawable.y if isinstance(drawable, Tree) else drawable.shadow_anchor[1]


def draw_scene(surface, player, bombs, shards, enemies, effects, camera, trees=()):
    """Depth-sort entities and trees by where they touch the ground, draw
    shadows, then sprites, then effects on top. A tree drawn over the frog
    is see-through so the frog never vanishes behind a canopy."""
    screen = surface.get_rect()
    visible_trees = [tree for tree in trees if tree_screen_rect(tree, camera).colliderect(screen)]
    drawables = _collect_entities(player, bombs, shards, enemies) + visible_trees
    drawables.sort(key=_ground_y)

    for tree in visible_trees:
        draw_tree_shadow(surface, tree, camera)
    for entity in drawables:
        if isinstance(entity, (Tree,) + _ENTITIES_WITH_BAKED_SHADOWS):
            continue
        sx, sy = camera.apply(*entity.shadow_anchor)
        draw_shadow(surface, sx, sy, entity.shadow_radius, entity.shadow_height_offset)

    player_rect = camera.apply_rect(player.rect) if player else None
    for drawable in drawables:
        if isinstance(drawable, Tree):
            covers_frog = (
                player_rect is not None
                and _ground_y(drawable) > _ground_y(player)
                and tree_screen_rect(drawable, camera).colliderect(player_rect)
            )
            draw_tree(surface, drawable, camera, faded=covers_frog)
            continue
        spec = _ENTITY_DRAW_SPECS.get(type(drawable))
        if spec:
            spec[0](surface, drawable, camera)

    for effect in effects:
        draw_explosion_effect(surface, effect, camera)


def draw_overlay(surface, bombs, camera):
    for bomb in bombs:
        if bomb.timer > 0:
            radius = int(bomb.radius * (1 - bomb.timer / BOMB_FUSE_MS) * 0.5 + 20)
            sx, sy = camera.apply(bomb.x, bomb.y)
            pygame.draw.circle(surface, (255, 170, 0, 40), (int(sx), int(sy)), radius, 1)
