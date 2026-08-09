# Bomb Frog Design Notes

## Fun combo

"Leapfrog with bombs" is doing a lot of work as a hook because it implies both a movement mechanic and an offense mechanic are the same button. Let's pull that thread.

## Core fantasy

You're not just dodging a bullet-hell pattern, you're using bombs to reposition through it — leapfrogging from safe spot to safe spot while the arena tries to fill in behind you with shrapnel.

## The central mechanic: bomb-leap

Instead of a dash, your primary mobility tool is a bomb-jump — you throw/place a bomb and leap off the blast to reach the next safe tile, similar to rocket-jumping but as your core traversal, not an exploit. This solves the classic bullet-hell problem where dodging is purely evasive and passive; here movement is offense, since the bomb also damages whatever's under it.

Design implications:
- Risk/reward on timing: leap too early, you undershoot and land in the blast radius yourself. Leap late, you eat the bullets you were trying to skip.
- Bombs have arc + fuse, so skilled play means pre-placing a bomb a beat before you need it, turning the whole game into a rhythm puzzle layered on top of dodging.
- Chaining: landing near a second bomb (yours or an enemy corpse's future explosion) lets you chain leaps — a skill-expression "no-hit run" loop, very Spire-ish in that mastery comes from reading the board a step ahead rather than raw reflexes.

## The shrapnel layer

This is your best idea and worth designing around explicitly: enemy death is not the end of the threat, it's a second bullet pattern.

- Each enemy type could have a distinct death-burst signature — a grunt might pop 6 shards in a ring, a heavier unit might spray a directional cone toward wherever it was facing, an elite might drop a delayed mine-shrapnel that goes off half a second later to punish greedy leaping.
- This means kill order matters — popping enemies in the wrong sequence stacks overlapping shrapnel fields you can't leap through cleanly. Good players will bait enemies into clusters and detonate them in a spot that clears the leap path, essentially using enemy corpses as terrain manipulation.
- You could let bomb-leaps catch shrapnel mid-flight as a high-skill parry — leaping through the shard ring at the right instant nets bonus currency/score, rewarding aggression instead of pure avoidance.

## Roguelike meta-layer ideas

- Bomb variants as your "deck": sticky bombs (delay + bigger leap arc), shard bombs (denser shrapnel, better area denial), null bombs (kill without shrapnel, for cleanup safety at a damage/cost tradeoff). Runs are built around which bomb types you draft, Spire-style.
- Leap upgrades that change the verb itself: double-leap (chain two jumps off one bomb), phase-leap (brief bullet immunity mid-arc), shrapnel-magnet (shards curve toward you slightly, for a build that leans into the parry-for-reward loop instead of avoiding it entirely).
- Room modifiers that mess with the leap/shrapnel interaction specifically — wind that drifts shrapnel, low-gravity rooms with longer arcs, "glass floor" rooms where landing off-target has its own penalty.

## Open design questions

A few open design questions worth pinning down early since they'll shape everything else:

1. Is the bomb-leap your only movement, or a supplement to normal dodging/movement? (Only-option is more distinctive but much less forgiving — worth prototyping both.)
2. Top-down or side-view? Side-view leapfrog reads more literally and lets gravity do work on the arc; top-down keeps the pure bullet-hell readability.
3. Does shrapnel deal chip damage or is it instant-death like classic bullet hell? That decision basically determines whether this is a "twitch precision" game or a "tense but forgiving" one.

## Next step offer

Want me to sketch out a rough enemy roster with specific shrapnel patterns, or storyboard a single arena encounter to see how the leap/shrapnel interplay actually plays out moment to moment?
