# Bomb Frog Design Notes

## Hook

"Leapfrog with bombs": movement and offense share one button. You use bombs to get
through the arena, hopping from safe spot to safe spot while it fills up with shrapnel
behind you.

## Implemented

What the game does today (code pointers in parentheses).

- **Top-down view, gravity on a jump axis.** You move freely with WASD/arrows, and Space
  jumps. The jump is a height offset over the ground, not a vertical move on screen
  (`game/simulation/player.py`).
- **Bombs launch at the jump apex.** Each jump spends a bomb, if one is available and off
  cooldown. You carry 2 and get one back per explosion (`bomb_launcher.py`,
  `BOMB_LIMIT`, `BOMB_COOLDOWN_MS`).
- **Bomb-leap.** An explosion pushes the frog away from the blast and upward, scaled by
  distance (`Player.apply_explosion`, `BOMB_FORCE`). It adds to normal movement rather
  than replacing it.
- **Detonation.** A bomb explodes once it has landed and its fuse is done, or the moment
  an enemy touches it. A bomb spawned on top of an enemy survives its first tick
  (`World._bomb_should_explode`). About 5% of bombs also throw a ring of shrapnel.
- **Airborne = safe.** Enemies and shards only hurt a grounded frog, so timing the jump
  is the core dodge.
- **The shrapnel layer.** Each enemy type has its own death pattern (`enemy_types.py`):
  | Enemy (sprite) | HP | Death shrapnel | Follow chance |
  |---|---|---|---|
  | grunt (badger) | 1 | ring of 6 | 30% |
  | heavy (boar) | 2 | 5-shard cone in the direction it faced | 20% |
  | elite (stag) | 3 | slower ring of 8 | 50% |
- **Some enemies chase.** Enemies walk side to side until the frog first comes within
  `ENEMY_NOTICE_RADIUS`. Then each one rolls its type's `follow_chance` once. A winner
  chases at walking speed until the frog is past `ENEMY_GIVE_UP_RADIUS`, then goes back
  to walking side to side for good (`Enemy._steer_toward`).
- **Shrapnel hurts enemies too**, so kill order and chain reactions matter.
- **Hurt enemies show it.** Multi-HP critters (boar, stag) blend toward red and limp with
  each hit, down to 60% speed on their last HP (`Enemy.injury`, `ENEMY_INJURY_SLOWDOWN`,
  `ENEMY_INJURY_TINT`).
- **Lives, not chip damage.** Any hit costs one of 3 lives and respawns the frog; score
  and lives carry over. Score is +1 per frame survived and +100 per kill.
- **Map editor** for painting isometric tile levels (`game/scene/editor_state.py`; spec in
  `docs/superpowers/specs/2026-09-06-map-editor-design.md`). Not yet used by gameplay.

## Settled design questions

1. **Is the bomb-leap the only movement?** No. It's a supplement to free WASD movement.
2. **Top-down or side-view?** Top-down, with the jump drawn as height above an
   isometric ground.
3. **Chip damage or instant death?** Each hit costs a life (3 per run). It's
   forgiving across a run but each hit still matters.

## Ideas — not built

Nothing below exists in code yet.

### Shrapnel

- An elite that drops a delayed mine-shrapnel which goes off half a second after it dies,
  to punish greedy leaping.
- Baiting enemies into clusters and detonating them so the shrapnel clears your leap path
  instead of blocking it (partly possible today; nothing in the design rewards it yet).
- Shrapnel parry: leaping through a shard ring at the right instant earns bonus
  currency/score, rewarding aggression over pure avoidance.

### Roguelike meta-layer

- **Bomb variants as a drafted "deck"**, Spire-style: sticky bombs (delay + bigger leap
  arc), shard bombs (denser shrapnel, better area denial), null bombs (kill without
  shrapnel, at a damage/cost tradeoff).
- **Leap upgrades** that change the verb: double-leap (two jumps off one bomb), phase-leap
  (brief immunity mid-arc), shrapnel-magnet (shards curve toward you, for a parry build).
- **Room modifiers** that bend the leap/shrapnel interaction: wind that drifts shrapnel,
  low-gravity rooms with longer arcs, "glass floor" rooms that punish off-target landings.

### Levels

- Load editor-authored levels in `World` instead of the generated arena.
- A fourth critter. Wolf art exists (`assets/critters/wolf/`) but has no `ENEMY_TYPES`
  entry.
