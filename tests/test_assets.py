import pygame

from game.rendering.assets import get_frog_frames, get_bomb_explosion_frames
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
