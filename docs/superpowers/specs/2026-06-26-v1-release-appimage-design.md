# Sub-project A: v1.0 Release + AppImage

Date: 2026-06-26

## Goal

Ship Q3N v1.0.0 as a GitHub release with three assets: AppImage, Debian package, source tarball. Provide a single local script that builds everything and uploads.

## File Layout

```
scripts/
  build-appimage.sh     # builds AppImage only, callable standalone
  release.sh            # full build + tag + GitHub upload
  q3n.spec              # PyInstaller spec
  AppDir/
    AppRun              # entrypoint (chmod +x)
    q3n.desktop         # freedesktop desktop entry
    q3n.png             # symlink or copy of web/public/favicon.png
```

```
build/                  # gitignored output dir
  dist/q3n/             # PyInstaller frozen app
  work/                 # PyInstaller work dir
  q3n-1.0.0.AppImage
  q3n-1.0.0.tar.gz
```

The Debian build outputs to `../` per dpkg convention (`../q3n_1.0.0-1_all.deb`).

## AppImage Build (`build-appimage.sh`)

1. Ensure `pyinstaller` is available (`pip install pyinstaller` if not)
2. Run `pyinstaller scripts/q3n.spec --distpath build/dist --workpath build/work`
3. Copy `build/dist/q3n/` into `scripts/AppDir/usr/bin/` structure
4. Copy `web/public/favicon.png` → `scripts/AppDir/q3n.png`
5. Download `appimagetool-x86_64.AppImage` into `scripts/` if not cached
6. Run `appimagetool scripts/AppDir build/q3n-{VERSION}.AppImage`

### PyInstaller spec (`q3n.spec`)

- Entry point: `gui/app.py`
- `datas`: includes `core/`, `gui/`, `art/`, `examples/`
- `console=False` (no terminal window)
- `name='q3n'`
- Hidden imports: PySide6 modules as needed

## Release Script (`release.sh`)

```
Usage: GITHUB_TOKEN=<pat> ./scripts/release.sh 1.0.0
```

Steps in order:

1. Validate version arg provided
2. Check `git status` is clean and on `main`
3. Call `build-appimage.sh` → `build/q3n-{VERSION}.AppImage`
4. Run `dpkg-buildpackage -us -uc -b` → `../q3n_{VERSION}-1_all.deb`
5. `git archive --format=tar.gz --prefix=q3n-{VERSION}/ HEAD` → `build/q3n-{VERSION}.tar.gz`
6. `git tag v{VERSION} && git push origin v{VERSION}`
7. POST to `https://api.github.com/repos/thuruht/q3n/releases` — creates draft release with tag `v{VERSION}`
8. Upload three assets via the release upload URL
9. Patch release to `draft=false`

PAT sourced from `GITHUB_TOKEN` env var. Script exits non-zero and prints clear error if any step fails.

## Assets

| File | Description |
|------|-------------|
| `q3n-{VERSION}.AppImage` | Self-contained Linux GUI bundle |
| `q3n_{VERSION}-1_all.deb` | Debian/Ubuntu package |
| `q3n-{VERSION}.tar.gz` | Source tarball (git archive) |

## What's Not In Scope

- CI automation (intentional — user prefers local release control)
- Windows/macOS builds
- Updating the Cloudflare download site URLs (those point to GitHub release assets which will resolve automatically once the release exists)

## Testing

- Run `build-appimage.sh` standalone, verify AppImage launches `q3n-gui`
- Run `release.sh` with `--dry-run` flag (skips tag + upload, prints what would happen)
- Verify all three assets appear on the GitHub release page
