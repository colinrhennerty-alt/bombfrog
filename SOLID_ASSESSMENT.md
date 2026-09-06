# SOLID Assessment — Bomb Frog

Reviewed: all files under `game/`, plus `main.py`. Test files were not scored (SOLID applies to production design, not tests) but were used to confirm module boundaries are actually exercised in isolation.

## Overall Score: 8.7 / 10

This is a small pygame project that reads like it went through a deliberate refactor pass — several docstrings explicitly explain *why* a responsibility was split out or moved, which is a strong signal of a codebase actively maintained with SOLID in mind rather than one graded after the fact.

---

## Per-principle scores

### Single Responsibility Principle — 9/10

Responsibilities are cleanly separated by layer and by concern:

- **Simulation vs. rendering vs. persistence vs. input** are hard-separated packages (`game/simulation`, `game/rendering`, `game/persistence`, `game/input`). [renderer.py](game/rendering/renderer.py) never mutates state; [world.py](game/simulation/world.py) never touches pygame drawing.
- **`Player` vs `BombLauncher`**: [bomb_launcher.py](game/simulation/bomb_launcher.py) was deliberately extracted from `Player` — bomb count/cooldown/apex-timing is "projectile-lifecycle bookkeeping, not player physics" (stated directly in the module docstring). `Player` delegates via thin properties ([player.py:54-76](game/simulation/player.py#L54-L76)) rather than re-implementing.
- **`World`** is decomposed into one method per concern per frame — `_update_player`, `_update_camera`, `_maybe_spawn_enemy`, `_update_bombs`, `_update_enemies`, `_update_shards`, `_update_effects` ([world.py:81-91](game/simulation/world.py#L81-L91)) — instead of one monolithic `update()`.
- **`GameApp`** owns only menu/playing state-machine transitions; it does not know about pygame events (that's `main.py` + `key_mapping.py`) or how frames get drawn.
- **`key_mapping.py`** is explicitly scoped to "raw key → abstract action name" and documents that it must *not* decide what an action means in context — that's `GameApp`'s job.

Minor deduction: `World._update_enemies` ([world.py:168-181](game/simulation/world.py#L168-L181)) mixes enemy movement, shard-damage checking, death handling, and player-collision/life-loss in one method — it's still readable, but it's the one place doing more than one thing per pass.

### Open/Closed Principle — 9/10

Two strong examples of extension-without-modification:

- **`ENEMY_TYPES`** ([enemy_types.py](game/simulation/enemy_types.py)) is pure data (`EnemyType` dataclass + `_ring`/`_cone` shrapnel-pattern factories). The module docstring states the intent directly: "Adding a new enemy type means adding one entry to ENEMY_TYPES — nothing else in the game needs to change."
- **`_DRAW_FUNCS` / `_DEBUG_BOX_COLORS`** dispatch dicts in [renderer.py:108-120](game/rendering/renderer.py#L108-L120) key off `type(entity)` instead of an if/elif chain — adding a new drawable entity type is one dict entry, not a new branch in `draw_scene`.

Slight deduction: `renderer.draw_scene`'s shadow-anchor logic special-cases circular vs. rect entities via `hasattr(entity, "radius")` ([renderer.py:149](game/rendering/renderer.py#L149)) — a small closed-for-modification gap; a third entity shape would need a new hasattr branch rather than a data-driven lookup.

### Liskov Substitution Principle — 8.5/10

There's no formal inheritance hierarchy in this codebase (no shared base class for `Bomb`/`Shard`/`Enemy`/`Player`), so classic LSP violations aren't really possible — but there is an *implicit* interface: every drawable/simulated entity is expected to expose `.rect`, `.x`, `.y`, and either `.radius` or `.width`/`.height`. All four entity classes honor this consistently (confirmed via `_DRAW_FUNCS`, `draw_debug_boxes`, and `draw_scene`, which treat all four polymorphically without type-specific special-casing beyond the circular/rect shadow-anchor split noted above).

Docking slightly because this shared contract is implicit/duck-typed rather than an explicit `Protocol` — nothing stops a future entity from omitting `.rect` and failing only at runtime in `draw_scene`.

### Interface Segregation Principle — 9/10

No fat interfaces anywhere — modules expose narrow, single-purpose functions:

- `game/utils.py` — just `clamp()` and `env_flag()`.
- `game/simulation/hitbox.py` — just `sync_rect()`.
- `game/simulation/camera.py` — `snap_to`, `follow`, `apply`, `apply_rect`, each doing one thing (the docstring on `follow` even explains precisely how it differs from `snap_to`).
- `BombLauncher` exposes exactly the operations `Player` needs (`tick_cooldown`, `try_launch`, `check_apex`, `cancel_pending`, `refill_one`) — no leaked internals.

Nothing to dock here — no consumer is forced to depend on methods it doesn't use.

### Dependency Inversion Principle — 8.5/10

- **Camera** ([camera.py](game/simulation/camera.py)) is pure math with no pygame dependency, explicitly documented as usable from both simulation and rendering — a good example of a shared abstraction neither side owns.
- **Simulation has zero pygame *drawing* dependency** — confirmed throughout `game/simulation/*` (pygame is only used for `Rect`, a data structure, never `Surface`/`display`).
- `World.update()` takes `keys, dt, now` as parameters rather than reading global state, and lazy-loaded asset caches (`assets.py`, `isometric_assets.py`) are deferred specifically to invert the dependency on `pygame.display` being initialized first.

Deduction: `Bomb.__init__` calls `random.random()` directly ([bomb.py:15](game/simulation/bomb.py#L15)) and `Enemy.__init__` calls `random.choices`/`random.uniform` directly ([enemy.py:17-19,40](game/simulation/enemy.py#L17-L19)) — wall-clock/global-RNG-style hidden dependencies that make these constructors harder to test deterministically without monkeypatching `random`. This is the one recurring DIP friction point in an otherwise well-inverted codebase (the test suite works around it rather than the production code exposing a seam).

---

## Notable strengths (evidence of SOLID-aware refactoring, not just accidental structure)

- Docstrings across `world.py`, `game_app.py`, `bomb_launcher.py`, and `key_mapping.py` explicitly state *why* a boundary exists — this is a codebase where responsibility splits were deliberate design decisions, not incidental.
- Save/load round-trips through explicit `from_dict`/`apply_dict`/`to_dict`-style methods on each entity, keeping serialization logic colocated with the type it serializes rather than centralized in `save_load.py` (which stays a thin dict-shuffling layer).
- `hitbox.sync_rect` is a single shared helper ensuring the collision rect and the rendered sprite position can never drift apart — a subtle correctness/SRP win in one place.

## Where a future pass would earn the most

1. ~~**`World._update_enemies`** — split enemy-movement, shard-collision, death, and player-collision handling into distinct steps.~~ **Applied**: split into `_advance_enemy` (movement/shard-damage/death) and `_enemy_hits_player` (the collision check), matching the existing `_update_bombs`/`_bomb_should_explode`/`_explode_bomb` pattern.
2. ~~**RNG as a hidden dependency** in `Bomb`/`Enemy` constructors.~~ **Applied**: both accept an optional `rng` parameter (defaulting to the `random` module), removing the DIP friction point and making both classes fully deterministic under test without monkeypatching.
3. ~~**An explicit `Entity` `Protocol`**.~~ **Applied**: `game/simulation/entity.py` declares a `runtime_checkable Entity` Protocol (`x`, `y`, `rect`, `shadow_anchor`), and each entity class now exposes an explicit `shadow_anchor` property. `renderer.draw_scene`'s shadow-anchor logic reads `entity.shadow_anchor` directly instead of branching on `hasattr(entity, "radius")`.

All three were applied via TDD (failing test confirmed red, then minimal implementation to green) except the mechanical `World` method split, which changed no observable behavior and was verified by full-suite green-before/green-after at the same test count. Full suite: 207 passing (was 195 before this pass).
