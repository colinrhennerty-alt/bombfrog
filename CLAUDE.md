# Bomb Frog

Top-down pygame arcade game: a frog that jumps over enemies and shrapnel, launching a
bomb at the apex of each jump. See README.md for controls, DESIGN.md for what's built vs.
planned.

## Commands

```bash
pip install -r requirements-dev.txt   # pygame + pytest
python3 main.py                        # run the game (`python` may not be on PATH)
BOMBFROG_DEBUG=1 python3 main.py       # start with hitbox overlay + debug log on
python3 -m pytest -q                   # full suite, headless
```

Tests run headlessly: `tests/conftest.py` sets the SDL dummy drivers and a 1x1 display.
CI (`.github/workflows/ci.yml`) runs the same `pytest` on every push and PR.

## Layers

| Package | Owns | Must not |
|---|---|---|
| `game/simulation/` | Round state and per-frame rules. `World` owns one round; `Player`, `Bomb`, `Shard`, `Enemy`, `Camera`, `Rect`, `TileMap` | Draw anything |
| `game/scene/` | Mode state machine (`GameApp`, modes in `modes.py`: menu ↔ playing ↔ editor) and `EditorState` | Touch pygame events or surfaces |
| `game/input/` | Raw pygame key → `Action` (`actions.py`), per `Mode` | Decide what an action means |
| `game/rendering/` | Drawing only, from simulation/scene state | Mutate game state |
| `game/persistence/` | JSON save files and level files | — |
| `main.py` | pygame init, event pump, picking what to draw | Hold game logic |

`game/config.py` holds every tuning constant. `game/paths.py` resolves asset and
user-data paths, including PyInstaller bundles.

## Invariants worth knowing

- **Sizes are relative to the frog.** `PLAYER_BASE_SIZE × ENTITY_SCALE` sets the frog;
  each `EnemyType.height_vs_frog` sizes enemies from it. Change `ENTITY_SCALE` to rescale
  everything. `tests/test_visual_size.py` pins how big things *read*.
- **The frog must be able to jump every enemy**: `tests/test_jump_clearance.py`.
- **Being airborne is the dodge.** Enemies and shards only hurt a grounded player.
- **`Rect` mimics pygame's**, including halving odd sizes with integer division.
- **New enemy = one entry in `ENEMY_TYPES`** (`game/simulation/enemy_types.py`); its
  death-shrapnel pattern is part of the entry.
- **Entities follow the `Entity` Protocol** (`game/simulation/entity.py`); the renderer
  relies on it instead of `hasattr` checks.
- Simulation takes `now`/`dt` as arguments and never reads the clock. Randomness goes
  through an injectable `rng` (`World`, `Enemy`, `Bomb`); tests pass a seeded one.

## Status

- The map editor (menu → Map Editor) paints and saves `LEVEL_FILE` (a user-data path,
  see `game/paths.py`), but `World` does not load levels yet; gameplay still uses a
  generated arena.
- `DESIGN.md` lists bomb variants, leap upgrades and room modifiers as unbuilt ideas.

## Workflow

- Tickets live in Linear (team Raining Potatoes, project "Bomb Frog").
- Behavior changes go test-first; pure refactors keep the existing suite green.
- Commit and push each ticket before calling it done. **Every push to `main` publishes a
  build to itch.io** (RELEASING.md), so keep `main` deployable.
- Tickets that change what players see need a `Release: patch|minor|major` label.
