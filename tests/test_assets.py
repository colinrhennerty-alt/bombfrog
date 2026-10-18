import pygame

from game.rendering.assets import get_frog_frames, get_bomb_explosion_frames, get_critter_frames
from game.config import FROG_IDLE_FRAME_COUNT


def test_get_bomb_explosion_frames_returns_the_expected_frame_set():
    frames = get_bomb_explosion_frames()
    assert len(frames) == 4
    assert all(isinstance(frame, pygame.Surface) for frame in frames)
    assert all(frame.get_size() == (32, 32) for frame in frames)


def test_get_frog_frames_returns_the_expected_frame_set():
    frames = get_frog_frames()
    assert len(frames["idle"]) == FROG_IDLE_FRAME_COUNT
    assert all(isinstance(f, pygame.Surface) for f in frames["idle"])
    assert isinstance(frames["jump"], pygame.Surface)
    assert isinstance(frames["land"], pygame.Surface)


def test_frog_frames_are_scaled_to_sprite_size():
    from game.rendering.assets import SPRITE_SIZE

    frames = get_frog_frames()
    assert frames["idle"][0].get_size() == (SPRITE_SIZE, SPRITE_SIZE)
    assert frames["jump"].get_size() == (SPRITE_SIZE, SPRITE_SIZE)
    assert frames["land"].get_size() == (SPRITE_SIZE, SPRITE_SIZE)


def test_get_frog_frames_is_cached_across_calls():
    first = get_frog_frames()
    second = get_frog_frames()
    assert first is second


def test_get_critter_frames_has_both_facings_with_each_critters_frame_count():
    frames = get_critter_frames()
    expected_counts = {"badger": 9, "boar": 4, "stag": 10}
    assert set(frames) == set(expected_counts)
    for critter, count in expected_counts.items():
        for facing in ("SE", "SW"):
            assert len(frames[critter][facing]) == count
            assert all(isinstance(f, pygame.Surface) for f in frames[critter][facing])


def test_get_critter_frames_is_cached_across_calls():
    assert get_critter_frames() is get_critter_frames()


def test_critter_frames_have_no_empty_rows_below_the_art():
    # Regression: the source frames carry transparent padding under the
    # critter's feet (6-8px of 32 on the badger), and draw_enemy scales the
    # whole frame into the hitbox — so the art floated above rect.bottom.
    # The lowest opaque row across a facing's frames must be its last row.
    for critter, facings in get_critter_frames().items():
        for facing, frames in facings.items():
            lowest = max(f.get_bounding_rect(min_alpha=1).bottom for f in frames)
            assert lowest == frames[0].get_height(), (critter, facing)


def test_critter_frames_within_a_facing_share_one_size():
    # A shared crop (not per-frame) keeps the art from jittering between frames.
    for critter, facings in get_critter_frames().items():
        for facing, frames in facings.items():
            assert len({f.get_size() for f in frames}) == 1, (critter, facing)
