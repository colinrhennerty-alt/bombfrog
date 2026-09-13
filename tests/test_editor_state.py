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
