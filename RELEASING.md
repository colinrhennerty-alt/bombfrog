# Releasing

Bomb Frog uses a simple version-tag-build-upload flow to ship to itch.io.

## Version scheme

The single source of truth for the version is `version` in [`pyproject.toml`](pyproject.toml), following [SemVer](https://semver.org/) (`MAJOR.MINOR.PATCH`). Bump it as:

- **PATCH** (`0.1.0` → `0.1.1`): bug fixes, no new content or gameplay changes.
- **MINOR** (`0.1.0` → `0.2.0`): new content or features (a new level, an enemy type, the map editor going live in-game, etc.).
- **MAJOR** (`0.x.y` → `1.0.0`): first "real" public release, or a breaking change to save files / level format.

Before `1.0.0`, expect frequent minor bumps as the game is still taking shape.

## Ticket labeling

Every Linear ticket whose completion should trigger a new shipped build must carry a `Release: patch`, `Release: minor`, or `Release: major` label, using the same rules as above. This is what decides the version bump when the release is cut: if any ticket since the last release is `major`, the release is major; else if any is `minor`, it's minor; otherwise it's a `patch` release. Pure infrastructure/tooling tickets that don't change what players experience (CI setup, docs, license audits) don't need this label.

## Release steps

1. **Bump the version** in `pyproject.toml` and commit it (`git commit -m "Bump version to X.Y.Z"`).
2. **Tag the release**: `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. **CI builds the platform archives.** Pushing a `v*` tag triggers the release workflow (see `.github/workflows/`, added in the CI ticket), which runs PyInstaller on Windows, macOS, and Linux runners and uploads each as a build artifact named `bombfrog-X.Y.Z-<platform>.zip`.
4. **Download the CI artifacts** from the workflow run and upload them to the [itch.io project page](https://itch.io) as new versions of the existing downloadable files, tagging each with its platform so itch.io shows the right download button per OS.
5. **Update the itch.io page changelog/devlog** with what changed in this version.
6. **Smoke-test** at least one downloaded build before publishing the update live (see the itch.io publish ticket for the full checklist).

## Manual release (before CI exists)

Until the CI build pipeline is set up, build locally instead of relying on step 3:

```bash
pip install -r requirements-dev.txt
pyinstaller bombfrog.spec
```

This produces a macOS build under `dist/bombfrog/`. Windows/Linux builds require running the same command on those platforms (or via CI once available) — PyInstaller does not cross-compile.
