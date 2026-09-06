# Interactive Map Editor — Design

## Context

Bomb Frog currently has no authored level content: the world is a fixed-size
procedural arena (`WORLD_WIDTH` x `WORLD_HEIGHT` from `game/config.py`) with a
uniform grass floor and a fixed-thickness stone border, computed purely by
`is_border_tile` in `game/rendering/renderer.py`. There is no tile-type
system beyond "grass vs. border stone," and no level file format.

The user wants an interactive, in-game tool to paint a ground layout using
the full isometric tileset (115 numbered tile images in
`assets/isometric tileset/separated images/`), and save/load that layout as
a level file. This round is scoped to the editor itself — tile painting,
palette selection, save/load to JSON — not to wiring an authored level into
actual gameplay (`World` continues to generate its own arena as it does
today). That wiring is a natural follow-up once this tool exists.

## Scope

**In scope:**
- A new `"editor"` mode reachable from the main menu.
- Free camera panning over the world-sized tile grid.
- A palette UI exposing all tile images found in the tileset folder.
- Click-to-paint a tile onto a grid cell; palette selection via click or
  keyboard.
- Save/load the painted grid to/from a JSON file under `levels/`.

**Out of scope (explicitly deferred):**
- Wiring saved levels into actual gameplay (`World` loading a `TileMap`).
- Entity placement (spawn points, enemies, items) — tile painting only.
- Undo/redo, multi-tile brushes, layers, or any painting tool beyond
  single-cell click-to-paint.

## Components

### 1. Tile palette loader — `game/rendering/isometric_assets.py`

Add a function that discovers every tile image in
`assets/isometric tileset/separated images/` (glob `tile_*.png`), loads and
scales each the same way `_load_tile` already does, and caches them keyed by
filename stem (e.g. `"tile_022"`). This is additive: `get_grass_tile()` and
`get_stone_tile()` are untouched and remain the gameplay defaults.

```python
def get_all_tiles():
    """Returns {tile_id: Surface} for every tile_*.png in the tileset
    folder, e.g. {"tile_000": Surface, "tile_001": Surface, ...}."""
```

Lazy + cached, consistent with the existing module's docstring rationale
(`Surface.convert_alpha()` needs an active display).

### 2. `TileMap` domain object — new `game/simulation/tilemap.py`

A plain grid of tile choices, independent of `World`:

```python
class TileMap:
    def __init__(self, width_tiles, height_tiles):
        self.width_tiles = width_tiles
        self.height_tiles = height_tiles
        self.cells = {}  # (col, row) -> tile_id string

    def set_tile(self, col, row, tile_id): ...
    def get_tile(self, col, row):  # None if unpainted
        ...
    def to_dict(self): ...

    @classmethod
    def from_dict(cls, data): ...
```

Serialized shape:

```json
{
  "width_tiles": 64,
  "height_tiles": 64,
  "cells": {"12,4": "tile_022", "13,4": "tile_063"}
}
```

Follows the existing `to_dict`/`from_dict` convention used by `Enemy` and
`World` (`game/simulation/enemy.py`, `game/simulation/world.py`).

### 3. `EditorState` — new `game/scene/editor_state.py`

Owns editor-only state, analogous to how `World` owns playing-state:

```python
class EditorState:
    def __init__(self, width_tiles, height_tiles, viewport_width, viewport_height):
        self.tilemap = TileMap(width_tiles, height_tiles)
        self.camera = Camera(viewport_width, viewport_height,
                              width_tiles * TILE_WIDTH, height_tiles * TILE_FOOTPRINT_HEIGHT)
        self.palette = list(get_all_tiles().keys())
        self.selected_index = 0
        self.hover_col = None
        self.hover_row = None
```

Behavior methods: `pan(dx, dy)`, `select_tile(index)`, `paint_at(col, row)`,
`save(path)`, `load(path)` (delegating to `TileMap`/a small `level_io`
save/load helper mirroring `game/persistence/save_load.py`'s plain
`json.dump`/`json.load` pattern).

Screen→tile coordinate inversion (for mouse clicks) reuses the same math
`ground_tile_screen_pos`/`visible_tile_range` already encode, inverted:
given a mouse `(mx, my)` and the camera, recover `(col, row)`.

### 4. `GameApp` state machine — `game/scene/game_app.py`

- Add `"Map Editor"` to `menu_options`.
- Add `"editor"` branch in `_confirm_menu_choice` that constructs an
  `EditorState` and sets `self.state = "editor"`.
- Add `_handle_editor_action` for editor-specific actions (pan, select
  tile, paint, save, load, back-to-menu), dispatched from `handle_action`
  alongside the existing menu/playing branches.
- Editor doesn't need a `tick`-driven update loop the way `World` does
  (painting is discrete, camera panning is direct) — `GameApp.tick` can
  simply skip when `state == "editor"`, same early-return shape it already
  has for non-"playing" states.

### 5. Input — `game/input/key_mapping.py`

Add an `EDITOR_KEY_ACTIONS` table (arrow keys/WASD → pan actions, number
keys → palette select, `S`/`L` → save/load, `ESC` → menu_back) and extend
`map_key`'s table lookup to branch on `state == "editor"`. Mouse clicks are
handled separately in `main.py` (pygame `MOUSEBUTTONDOWN`), translated to a
`paint` call via `EditorState`'s coordinate inversion — key_mapping stays
keyboard-only as it is today.

### 6. Rendering — `game/rendering/renderer.py`

New `draw_editor(surface, editor_state)` function, parallel to
`draw_ground`: iterates the same visible tile range, looks up each cell via
`editor_state.tilemap.get_tile(col, row)` (falling back to a neutral
"empty" placeholder tile when unpainted, rather than grass — keeps painted
vs. unpainted visually distinct), and draws:
- The tile grid itself.
- A hover highlight outline on the cell under the cursor.
- A palette strip (thumbnails of all tile images, highlighting the
  selected one).

### 7. Main loop — `main.py`

Add an `elif app.state == "editor":` branch calling `draw_editor`, and
extend the event loop to translate `MOUSEBUTTONDOWN` into a paint call when
`app.state == "editor"`.

### 8. Persistence — `levels/` directory

New sibling to the existing single `savegame.json`. A small helper (or
reuse of `game/persistence/save_load.py`'s pattern) writes/reads
`levels/<name>.json` via plain `json.dump`/`json.load`, matching the
existing persistence style — no new dependency.

## Testing

Unit tests (pygame-free where possible, following `tests/` mirror
structure):
- `TileMap.to_dict`/`from_dict` round-trip, including unpainted cells.
- Tile palette discovery: globbing returns all files, caching behaves
  (same object returned on second call).
- Screen↔tile coordinate inversion: given a known camera position and
  mouse coordinate, the recovered `(col, row)` matches the tile that
  `ground_tile_screen_pos` would have placed there.
- `EditorState.paint_at`/`select_tile`/`pan` behavior in isolation.

Manual verification (rendering/pygame window isn't unit-testable):
run the game, enter "Map Editor" from the menu, pan the camera, paint a
few tiles from different parts of the palette, save, return to menu,
re-enter editor, load the file back, confirm the grid matches.

## Follow-up (not this round)

- `World.from_level(tilemap)` or similar, to make `World` draw a `TileMap`
  instead of (or blended with) its procedural border/grass rule.
- Entity placement in the editor (player spawn, enemy spawn points).
