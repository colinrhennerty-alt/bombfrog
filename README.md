# Bomb Frog

A simple arcade-style game built with `pygame`.

## How to run

1. Install Python 3.
2. Install `pygame`:

```bash
pip install pygame
```

3. Run the game:

```bash
python main.py
```

## Controls

- Left / A: move left
- Right / D: move right
- Space / Up / W: jump
- R: restart after game over
- Esc: quit

## Goal

Avoid falling bombs and survive as long as possible.

## Tests

Install dev dependencies and run the test suite with `pytest`:

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run headlessly (no window pops up) via the SDL dummy video driver, configured in `tests/conftest.py`.
