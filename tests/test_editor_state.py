from game.config import WIDTH, HEIGHT, EDITOR_SIDEBAR_WIDTH
from game.scene.editor_state import EditorState
from game.rendering.isometric_assets import get_all_tiles
from game.rendering.renderer import ground_tile_screen_pos, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT


def test_starts_with_an_empty_tilemap():
    editor = EditorState()
    assert editor.tilemap.get_tile(5, 5) is None


def test_palette_includes_every_discovered_tile():
    editor = EditorState()
    assert set(editor.palette) == set(get_all_tiles().keys())


def test_selected_tile_id_starts_at_first_palette_entry():
    editor = EditorState()
    assert editor.selected_tile_id == editor.palette[0]


def test_select_tile_changes_the_selected_tile_id():
    editor = EditorState()
    editor.select_tile(3)
    assert editor.selected_tile_id == editor.palette[3]


def test_select_tile_out_of_range_is_a_noop():
    editor = EditorState()
    before = editor.selected_index
    editor.select_tile(len(editor.palette) + 100)
    assert editor.selected_index == before
    editor.select_tile(-1)
    assert editor.selected_index == before


def test_pan_moves_the_camera():
    editor = EditorState()
    editor.camera.x, editor.camera.y = 500, 500
    editor.pan(32, -16)
    assert editor.camera.x == 532
    assert editor.camera.y == 484


def test_pan_clamps_to_world_bounds():
    editor = EditorState()
    editor.pan(-10000, -10000)
    assert editor.camera.x == 0
    assert editor.camera.y == 0


def test_set_hover_updates_hover_col_and_row():
    editor = EditorState()
    editor.camera.x, editor.camera.y = 0, 0
    sx, sy = ground_tile_screen_pos(5, 3, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=3)
    editor.set_hover(sx + TILE_WIDTH / 2, sy + TILE_FOOTPRINT_HEIGHT / 4)
    assert (editor.hover_col, editor.hover_row) == (5, 3)


def test_paint_at_screen_sets_the_selected_tile_at_the_clicked_cell():
    editor = EditorState()
    editor.camera.x, editor.camera.y = 0, 0
    editor.select_tile(2)

    sx, sy = ground_tile_screen_pos(7, 4, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=4)
    editor.paint_at_screen(sx + TILE_WIDTH / 2, sy + TILE_FOOTPRINT_HEIGHT / 4)

    assert editor.tilemap.get_tile(7, 4) == editor.palette[2]


def test_save_and_load_round_trip(tmp_path):
    editor = EditorState()
    editor.camera.x, editor.camera.y = 0, 0
    editor.select_tile(1)
    sx, sy = ground_tile_screen_pos(2, 1, TILE_WIDTH, TILE_FOOTPRINT_HEIGHT, world_row=1)
    editor.paint_at_screen(sx + TILE_WIDTH / 2, sy + TILE_FOOTPRINT_HEIGHT / 4)

    save_path = str(tmp_path / "level.json")
    editor.save(save_path)

    other = EditorState()
    other.load(save_path)

    assert other.tilemap.get_tile(2, 1) == editor.palette[1]


def test_load_missing_file_is_a_noop():
    editor = EditorState()
    editor.tilemap.set_tile(1, 1, "tile_005")

    editor.load("/does/not/exist.json")

    assert editor.tilemap.get_tile(1, 1) == "tile_005"


# --- Sidebar layout / hit-testing -----------------------------------------


def test_camera_viewport_is_shrunk_by_the_sidebar_width():
    editor = EditorState(WIDTH, HEIGHT)
    assert editor.camera.viewport_width == WIDTH - EDITOR_SIDEBAR_WIDTH
    assert editor.camera.viewport_height == HEIGHT


def test_point_is_in_sidebar_true_at_and_past_the_map_viewport_edge():
    editor = EditorState(WIDTH, HEIGHT)
    assert editor.point_is_in_sidebar(editor.camera.viewport_width, 10) is True
    assert editor.point_is_in_sidebar(editor.camera.viewport_width + 50, 10) is True


def test_point_is_in_sidebar_false_within_the_map_viewport():
    editor = EditorState(WIDTH, HEIGHT)
    assert editor.point_is_in_sidebar(0, 0) is False
    assert editor.point_is_in_sidebar(editor.camera.viewport_width - 1, 10) is False


def test_palette_layout_has_an_entry_for_every_palette_tile():
    editor = EditorState(WIDTH, HEIGHT)
    assert set(editor.palette_layout.keys()) == set(editor.palette)


def test_palette_layout_rects_are_all_within_the_sidebar_region():
    editor = EditorState(WIDTH, HEIGHT)
    for x, y, w, h in editor.palette_layout.values():
        assert x >= editor.camera.viewport_width
        assert x + w <= WIDTH
        assert y >= 0
        assert y + h <= HEIGHT


def test_palette_layout_rects_do_not_overlap():
    editor = EditorState(WIDTH, HEIGHT)
    rects = list(editor.palette_layout.values())
    for i, (x1, y1, w1, h1) in enumerate(rects):
        for x2, y2, w2, h2 in rects[i + 1:]:
            overlaps_x = x1 < x2 + w2 and x2 < x1 + w1
            overlaps_y = y1 < y2 + h2 and y2 < y1 + h1
            assert not (overlaps_x and overlaps_y)


def test_save_and_load_button_rects_are_within_the_sidebar_region():
    editor = EditorState(WIDTH, HEIGHT)
    for x, y, w, h in (editor.save_button_rect, editor.load_button_rect):
        assert x >= editor.camera.viewport_width
        assert x + w <= WIDTH
        assert y >= 0
        assert y + h <= HEIGHT


def test_save_and_load_buttons_do_not_overlap_each_other():
    editor = EditorState(WIDTH, HEIGHT)
    x1, y1, w1, h1 = editor.save_button_rect
    x2, y2, w2, h2 = editor.load_button_rect
    overlaps_x = x1 < x2 + w2 and x2 < x1 + w1
    overlaps_y = y1 < y2 + h2 and y2 < y1 + h1
    assert not (overlaps_x and overlaps_y)


# --- handle_sidebar_click ---------------------------------------------------


def _center(rect):
    x, y, w, h = rect
    return x + w / 2, y + h / 2


def test_handle_sidebar_click_outside_any_control_returns_none():
    editor = EditorState(WIDTH, HEIGHT)
    # far outside every rect: near the very bottom-right corner
    assert editor.handle_sidebar_click(WIDTH - 1, HEIGHT - 1) is None


def test_handle_sidebar_click_on_a_palette_tile_selects_it():
    editor = EditorState(WIDTH, HEIGHT)
    target_tile_id = editor.palette[5]
    click_x, click_y = _center(editor.palette_layout[target_tile_id])

    result = editor.handle_sidebar_click(click_x, click_y)

    assert result == "select"
    assert editor.selected_tile_id == target_tile_id


def test_handle_sidebar_click_on_save_button_returns_save():
    editor = EditorState(WIDTH, HEIGHT)
    click_x, click_y = _center(editor.save_button_rect)
    assert editor.handle_sidebar_click(click_x, click_y) == "save"


def test_handle_sidebar_click_on_load_button_returns_load():
    editor = EditorState(WIDTH, HEIGHT)
    click_x, click_y = _center(editor.load_button_rect)
    assert editor.handle_sidebar_click(click_x, click_y) == "load"


def test_handle_sidebar_click_does_not_change_selection_when_missing_a_control():
    editor = EditorState(WIDTH, HEIGHT)
    before = editor.selected_index
    editor.handle_sidebar_click(WIDTH - 1, HEIGHT - 1)
    assert editor.selected_index == before


# --- drag painting -----------------------------------------------------------


def test_starts_not_dragging():
    editor = EditorState()
    assert editor.is_dragging is False
