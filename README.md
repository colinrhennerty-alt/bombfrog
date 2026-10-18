# Bomb Frog

A top-down arcade game built with `pygame`. You're a frog in an arena that keeps
filling with critters. Jumping is both your dodge and your weapon: at the top of each
jump you drop a bomb, and enemies that die burst into shrapnel you then have to avoid.

## How to play

- Enemies and shrapnel only hurt you while you're **on the ground**. Being airborne is
  how you dodge.
- Each jump launches a bomb at its apex, if you have one. You carry up to 2, and you get
  one back each time a bomb explodes.
- A bomb goes off once it has landed and its fuse runs out, or as soon as an enemy
  touches it. The blast also pushes you, so you can use it to leap.
- Each enemy type bursts into its own shrapnel pattern when it dies. Shrapnel hurts other
  enemies too.
- Tougher enemies turn red and slow down as you wear them down. Some enemies start chasing
  you if you get close.
- You have 3 lives. Score goes up the longer you survive, with +100 per kill.

## Controls

**Menu**

| Key | Action |
|---|---|
| Up / Down | Choose option |
| Enter / Space | Confirm |

**Playing**

| Key | Action |
|---|---|
| Arrows / WASD | Move |
| Space | Jump (launches a bomb at the apex). Restarts after game over |
| R | Restart after game over |
| F5 / F9 | Save / load the current round |
| Esc | Back to menu |
| F13 | Toggle hitbox debug overlay |

**Map editor** (menu → Map Editor)

| Input | Action |
|---|---|
| Arrows / WASD | Pan the camera |
| 1–9, 0 | Select one of the first ten tiles |
| Click a sidebar tile | Select that tile |
| Click / drag on the map | Paint the selected tile |
| Sidebar Wall Mode | Toggle whether painted tiles are walls |
| Sidebar Reset (click twice) | Clear the whole map |
| Sidebar Save / Load | Write or read the level file |
| Esc | Back to menu |

Saved levels aren't used in gameplay yet.

## How to run

Requires Python 3.12+.

```bash
pip install -r requirements.txt
python3 main.py
```

Set `BOMBFROG_DEBUG=1` to start with the debug overlay and logging on.

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```

Tests run headlessly (no window opens) using the SDL dummy video driver, configured in
`tests/conftest.py`.

## Releasing

See [RELEASING.md](RELEASING.md) for the version scheme and release process.
