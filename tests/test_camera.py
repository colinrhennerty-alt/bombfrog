"""Tests for the camera's deadzone-based follow() and hard snap_to().

follow() is the per-frame call during normal play: the camera should
stay put while the target is within a centered deadzone box on screen,
and only move enough to keep the target pinned at the box's edge once
it exits. snap_to() is the hard recenter used for one-time events
(respawn, load) where the camera should jump immediately instead.
"""

from game.simulation.camera import Camera

WIDTH, HEIGHT = 1700, 900
WORLD_WIDTH, WORLD_HEIGHT = WIDTH * 4, HEIGHT * 4


def _camera():
    return Camera(WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT)


def test_snap_to_centers_the_camera_exactly_on_the_target():
    camera = _camera()
    camera.snap_to(2000, 1500)
    assert camera.x == 2000 - WIDTH / 2
    assert camera.y == 1500 - HEIGHT / 2


def test_follow_does_not_move_the_camera_while_target_is_within_the_deadzone():
    camera = _camera()
    camera.snap_to(2000, 1500)
    before_x, before_y = camera.x, camera.y

    # A small move, well within a centered deadzone box.
    camera.follow(2010, 1505)

    assert camera.x == before_x
    assert camera.y == before_y


def test_follow_moves_the_camera_once_target_exits_the_deadzone_to_the_right():
    camera = _camera()
    camera.snap_to(2000, 1500)

    # Move the target far enough right to exit the deadzone box.
    camera.follow(2000 + WIDTH, 1500)

    assert camera.x > 2000 - WIDTH / 2  # camera actually moved right


def test_follow_pins_the_target_at_the_deadzones_right_edge_not_screen_center():
    camera = _camera()
    camera.snap_to(2000, 1500)

    camera.follow(2000 + WIDTH, 1500)

    # The target's screen-space x should now sit at the deadzone's right
    # edge, not back at the screen's horizontal center (that would just
    # be the old always-centered behavior).
    screen_x = (2000 + WIDTH) - camera.x
    deadzone_half_width = (WIDTH * 0.4) / 2
    assert screen_x == WIDTH / 2 + deadzone_half_width


def test_follow_moves_the_camera_left_once_target_exits_the_deadzone_to_the_left():
    camera = _camera()
    camera.snap_to(2000, 1500)

    camera.follow(2000 - WIDTH, 1500)

    assert camera.x < 2000 - WIDTH / 2


def test_follow_moves_the_camera_down_once_target_exits_the_deadzone_below():
    camera = _camera()
    camera.snap_to(2000, 1500)

    camera.follow(2000, 1500 + HEIGHT)

    assert camera.y > 1500 - HEIGHT / 2


def test_follow_moves_the_camera_up_once_target_exits_the_deadzone_above():
    camera = _camera()
    camera.snap_to(2000, 1500)

    camera.follow(2000, 1500 - HEIGHT)

    assert camera.y < 1500 - HEIGHT / 2


def test_follow_still_clamps_to_world_bounds():
    camera = _camera()
    camera.snap_to(2000, 1500)

    camera.follow(0, 0)  # far outside the deadzone, toward the world origin

    assert camera.x >= 0
    assert camera.y >= 0


def test_follow_clamps_to_the_far_world_edge():
    camera = _camera()
    camera.snap_to(WORLD_WIDTH - 2000, WORLD_HEIGHT - 1500)

    camera.follow(WORLD_WIDTH, WORLD_HEIGHT)

    assert camera.x <= WORLD_WIDTH - WIDTH
    assert camera.y <= WORLD_HEIGHT - HEIGHT
