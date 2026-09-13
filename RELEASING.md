# Releasing

Every push to `main` automatically builds and publishes to itch.io — there is no manual tag/release step.

## Version scheme

The single source of truth for the version is `version` in [`pyproject.toml`](pyproject.toml), following [SemVer](https://semver.org/) (`MAJOR.MINOR.PATCH`). Bump it as:

- **PATCH** (`0.1.0` → `0.1.1`): bug fixes, no new content or gameplay changes.
- **MINOR** (`0.1.0` → `0.2.0`): new content or features (a new level, an enemy type, the map editor going live in-game, etc.).
- **MAJOR** (`0.x.y` → `1.0.0`): first "real" public release, or a breaking change to save files / level format.

Before `1.0.0`, expect frequent minor bumps as the game is still taking shape.

## Ticket labeling

Every Linear ticket whose completion should trigger a new shipped build must carry a `Release: patch`, `Release: minor`, or `Release: major` label, using the same rules as above. This is what decides the version bump when the release is cut: if any ticket since the last release is `major`, the release is major; else if any is `minor`, it's minor; otherwise it's a `patch` release. Pure infrastructure/tooling tickets that don't change what players experience (CI setup, docs, license audits) don't need this label.

## Release steps

1. **Bump the version** in `pyproject.toml` when the change warrants it (see the version scheme above) and commit it (`git commit -m "Bump version to X.Y.Z"`).
2. **Merge/push to `main`.** Every push to `main` triggers the release workflow (`.github/workflows/release.yml`), which runs PyInstaller on Windows, macOS, and Linux runners, uploads each as a GitHub Actions build artifact, and pushes each platform's build directly to the [itch.io project's](https://bjorndead.itch.io/bomb-frog) `linux`/`win64`/`macos` channels via `butler`. The published `--userversion` is `pyproject.toml`'s version plus the short commit SHA (e.g. `0.1.0+abc1234`), so every push is distinguishable on itch.io even between version bumps.
3. **Update the itch.io page changelog/devlog** with what changed, when a bump warrants a visible note to players.
4. **Smoke-test** at least one downloaded build before flipping the page live (see the itch.io publish ticket for the full checklist) — publishing to itch.io's build channels does not by itself make the page public.

Since every push to `main` publishes automatically, keep `main` deployable — don't merge work you don't want live on itch.io immediately.

## macOS build notes

The macOS build is packaged as `Bomb Frog.app` (via `BUNDLE()` in `bombfrog.spec`), not a bare executable. PyInstaller ad-hoc signs it automatically during the build — there's no Apple Developer account involved, so Gatekeeper will still show one "cannot verify" warning on first launch. Players can proceed via right-click → Open, or System Settings → Privacy & Security → "Open Anyway". Without the `.app` wrapper, macOS previously Gatekeeper-checked every internal `.so`/`.framework` file individually, producing a flood of separate warnings instead of one.
