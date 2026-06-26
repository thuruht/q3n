# v1.0 Release + AppImage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `scripts/build-appimage.sh` that produces a self-contained Linux AppImage, and a `scripts/release.sh` that builds all three assets (AppImage, .deb, .tar.gz) and uploads them to a GitHub release.

**Architecture:** PyInstaller freezes the PySide6 GUI into a one-dir bundle; appimagetool wraps it into a portable AppImage. `release.sh` orchestrates both builds, tags git, and uploads via the GitHub Releases API using curl. No CI — everything runs locally.

**Tech Stack:** PyInstaller, appimagetool, bash, GitHub Releases API (curl + `GITHUB_TOKEN`)

## Global Constraints

- Repo: `thuruht/q3n`, default branch `main`
- Release tag format: `v{VERSION}` (e.g. `v1.0.0`)
- Asset filenames: `q3n-{VERSION}.AppImage`, `q3n_{VERSION}-1_all.deb`, `q3n-{VERSION}.tar.gz`
- Icon source: `web/public/favicon.png` (256×256 PNG, already exists)
- PAT always sourced from `GITHUB_TOKEN` env var — never hardcoded
- `build/` is already gitignored; `scripts/AppDir/` and `scripts/q3n.spec` must be tracked
- Repo root assumed to be the working directory when running scripts

---

### Task 1: Fix .gitignore + scaffold AppDir

**.gitignore currently has two overly-broad rules that would hide source files:**
- `AppDir/` — matches `scripts/AppDir/` (should only block build output)
- `*.spec` — matches `scripts/q3n.spec` (PyInstaller spec is source, not output)

**Files:**
- Modify: `.gitignore`
- Create: `scripts/AppDir/AppRun`
- Create: `scripts/AppDir/q3n.desktop`

- [ ] **Step 1: Fix .gitignore**

In `.gitignore`, replace:
```
AppDir/
*.spec
```
with:
```
build/AppDir/
scripts/appimagetool-x86_64.AppImage
```

(The `scripts/q3n.spec` we're about to create must be tracked. The cached appimagetool binary must not be.)

- [ ] **Step 2: Create `scripts/AppDir/AppRun`**

```bash
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "${HERE}/usr/opt/q3n/q3n" "$@"
```

Then make it executable:
```bash
chmod +x scripts/AppDir/AppRun
```

- [ ] **Step 3: Create `scripts/AppDir/q3n.desktop`**

```ini
[Desktop Entry]
Type=Application
Name=Q3N Manager
Exec=q3n
Icon=q3n
Comment=Browse and edit Q3N quote collections
Categories=Office;Database;TextTools;
Terminal=false
MimeType=application/x-q3n;
```

- [ ] **Step 4: Verify git sees the new files**

```bash
git status
```

Expected: `.gitignore` modified; `scripts/AppDir/AppRun` and `scripts/AppDir/q3n.desktop` as untracked new files. `scripts/appimagetool-x86_64.AppImage` should NOT appear (it doesn't exist yet, but the rule is in place).

- [ ] **Step 5: Commit**

```bash
git add .gitignore scripts/AppDir/AppRun scripts/AppDir/q3n.desktop
git commit -m "feat: scaffold AppDir and fix .gitignore for release tooling"
```

---

### Task 2: PyInstaller spec

**Files:**
- Create: `scripts/q3n.spec`

**Interfaces:**
- Produces: `build/dist/q3n/q3n` (executable) + `build/dist/q3n/_internal/` or sibling `.so` files (PyInstaller deps)

- [ ] **Step 1: Create `scripts/q3n.spec`**

```python
# scripts/q3n.spec
from pathlib import Path

block_cipher = None
repo_root = Path(SPECPATH).parent  # SPECPATH is scripts/, so parent is repo root

a = Analysis(
    [str(repo_root / 'gui' / 'app.py')],
    pathex=[str(repo_root)],
    binaries=[],
    datas=[
        (str(repo_root / 'core'), 'core'),
        (str(repo_root / 'gui'), 'gui'),
        (str(repo_root / 'art'), 'art'),
        (str(repo_root / 'examples'), 'examples'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtUiTools',
        'PySide6.QtSvg',
        'PySide6.QtPrintSupport',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='q3n',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='q3n',
)
```

- [ ] **Step 2: Smoke-test the spec (optional but recommended)**

```bash
pip install pyinstaller
python3 -m PyInstaller scripts/q3n.spec --distpath build/dist --workpath build/work --noconfirm
```

Expected: `build/dist/q3n/q3n` exists and is executable. Run it:
```bash
build/dist/q3n/q3n &
```
Expected: Q3N GUI opens. Kill it, continue.

- [ ] **Step 3: Commit**

```bash
git add scripts/q3n.spec
git commit -m "feat: add PyInstaller spec for AppImage build"
```

---

### Task 3: build-appimage.sh

**Files:**
- Create: `scripts/build-appimage.sh`

**Interfaces:**
- Consumes: `scripts/q3n.spec`, `scripts/AppDir/`, `web/public/favicon.png`
- Produces: `build/q3n-{VERSION}.AppImage`

- [ ] **Step 1: Create `scripts/build-appimage.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: build-appimage.sh <version>}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="$REPO_ROOT/scripts"
BUILD_DIR="$REPO_ROOT/build"
APPDIR="$SCRIPTS_DIR/AppDir"
APPIMAGETOOL="$SCRIPTS_DIR/appimagetool-x86_64.AppImage"
DIST_DIR="$BUILD_DIR/dist/q3n"

echo "==> Building AppImage for Q3N v${VERSION}"
mkdir -p "$BUILD_DIR"

# Ensure PyInstaller is available
python3 -c "import PyInstaller" 2>/dev/null || pip install pyinstaller

# Freeze the app
echo "==> Running PyInstaller..."
cd "$REPO_ROOT"
python3 -m PyInstaller \
    scripts/q3n.spec \
    --distpath build/dist \
    --workpath build/work \
    --noconfirm

# Assemble AppDir: put PyInstaller bundle under usr/opt/q3n/
echo "==> Assembling AppDir..."
rm -rf "$APPDIR/usr"
mkdir -p "$APPDIR/usr/opt"
cp -r "$DIST_DIR" "$APPDIR/usr/opt/q3n"

# Copy icon
cp "$REPO_ROOT/web/public/favicon.png" "$APPDIR/q3n.png"

# Download appimagetool if not cached
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "==> Downloading appimagetool..."
    curl -Lo "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

# Build AppImage
echo "==> Running appimagetool..."
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$BUILD_DIR/q3n-${VERSION}.AppImage"

echo "==> Done: $BUILD_DIR/q3n-${VERSION}.AppImage"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/build-appimage.sh
```

- [ ] **Step 3: Test the build**

```bash
./scripts/build-appimage.sh 1.0.0
```

Expected output ends with:
```
==> Done: /home/.../build/q3n-1.0.0.AppImage
```

- [ ] **Step 4: Test the AppImage launches**

```bash
./build/q3n-1.0.0.AppImage
```

Expected: Q3N GUI opens. If it fails with a missing library error, add the library name to `hiddenimports` in `scripts/q3n.spec` and repeat from Step 3.

- [ ] **Step 5: Commit**

```bash
git add scripts/build-appimage.sh
git commit -m "feat: add build-appimage.sh (PyInstaller + appimagetool)"
```

---

### Task 4: release.sh

**Files:**
- Create: `scripts/release.sh`

**Interfaces:**
- Consumes: `scripts/build-appimage.sh`, `GITHUB_TOKEN` env var
- Produces: GitHub release at `https://github.com/thuruht/q3n/releases/tag/v{VERSION}` with three uploaded assets

- [ ] **Step 1: Create `scripts/release.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: GITHUB_TOKEN=<pat> ./scripts/release.sh <version> [--dry-run]}"
DRY_RUN=false
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN=true

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build"
REPO="thuruht/q3n"

APPIMAGE="$BUILD_DIR/q3n-${VERSION}.AppImage"
DEB="$REPO_ROOT/../q3n_${VERSION}-1_all.deb"
TARBALL="$BUILD_DIR/q3n-${VERSION}.tar.gz"

: "${GITHUB_TOKEN:?GITHUB_TOKEN env var is required}"

echo "==> Q3N Release v${VERSION}${DRY_RUN:+ (DRY RUN)}"

# 1. Validate git state
if [ "$DRY_RUN" = false ]; then
    if ! git -C "$REPO_ROOT" diff --quiet || ! git -C "$REPO_ROOT" diff --cached --quiet; then
        echo "ERROR: Working tree is not clean. Commit or stash changes first." >&2
        exit 1
    fi
    BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
    if [ "$BRANCH" != "main" ]; then
        echo "ERROR: Must be on main branch (currently on '$BRANCH')." >&2
        exit 1
    fi
fi

# 2. Build AppImage
echo "==> Building AppImage..."
"$REPO_ROOT/scripts/build-appimage.sh" "$VERSION"

# 3. Build .deb
echo "==> Building Debian package..."
cd "$REPO_ROOT"
dpkg-buildpackage -us -uc -b
if [ ! -f "$DEB" ]; then
    echo "ERROR: Expected .deb not found at $DEB" >&2
    exit 1
fi

# 4. Create source tarball
echo "==> Creating source tarball..."
mkdir -p "$BUILD_DIR"
git -C "$REPO_ROOT" archive \
    --format=tar.gz \
    --prefix="q3n-${VERSION}/" \
    HEAD > "$TARBALL"

echo "==> Assets ready:"
echo "    AppImage: $APPIMAGE"
echo "    .deb:     $DEB"
echo "    tarball:  $TARBALL"

if [ "$DRY_RUN" = true ]; then
    echo "==> DRY RUN complete. Would now: tag v${VERSION}, create GitHub release, upload assets."
    exit 0
fi

# 5. Tag and push
echo "==> Tagging v${VERSION}..."
git -C "$REPO_ROOT" tag "v${VERSION}"
git -C "$REPO_ROOT" push origin "v${VERSION}"

# 6. Create draft GitHub release
echo "==> Creating GitHub release (draft)..."
RELEASE_JSON=$(curl -sf -X POST \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"tag_name\": \"v${VERSION}\",
        \"name\": \"Q3N v${VERSION}\",
        \"draft\": true,
        \"body\": \"Q3N v${VERSION}\n\n**Assets:**\n- \`.AppImage\` — Linux GUI (self-contained, no install needed)\n- \`.deb\` — Debian/Ubuntu package\n- \`.tar.gz\` — Source tarball\"
    }" \
    "https://api.github.com/repos/${REPO}/releases")

RELEASE_ID=$(echo "$RELEASE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
UPLOAD_BASE="https://uploads.github.com/repos/${REPO}/releases/${RELEASE_ID}/assets"

# 7. Upload assets
_upload() {
    local file="$1"
    local name="$2"
    echo "==> Uploading $name..."
    curl -sf -X POST \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Content-Type: application/octet-stream" \
        --data-binary "@${file}" \
        "${UPLOAD_BASE}?name=${name}" > /dev/null
    echo "    Uploaded: $name"
}

_upload "$APPIMAGE"  "q3n-${VERSION}.AppImage"
_upload "$DEB"       "q3n_${VERSION}-1_all.deb"
_upload "$TARBALL"   "q3n-${VERSION}.tar.gz"

# 8. Publish (undraft)
echo "==> Publishing release..."
curl -sf -X PATCH \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"draft": false}' \
    "https://api.github.com/repos/${REPO}/releases/${RELEASE_ID}" > /dev/null

echo "==> Release published: https://github.com/${REPO}/releases/tag/v${VERSION}"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/release.sh
```

- [ ] **Step 3: Dry-run test**

```bash
./scripts/release.sh 1.0.0 --dry-run
```

Expected output (approximate):
```
==> Q3N Release v1.0.0 (DRY RUN)
==> Building AppImage...
...
==> Assets ready:
    AppImage: .../build/q3n-1.0.0.AppImage
    .deb:     .../q3n_1.0.0-1_all.deb
    tarball:  .../build/q3n-1.0.0.tar.gz
==> DRY RUN complete. Would now: tag v1.0.0, create GitHub release, upload assets.
```

- [ ] **Step 4: Commit**

```bash
git add scripts/release.sh
git commit -m "feat: add release.sh — build + tag + GitHub upload"
```

- [ ] **Step 5: Cut the actual release**

```bash
GITHUB_TOKEN=<your-pat> ./scripts/release.sh 1.0.0
```

Expected: ends with `==> Release published: https://github.com/thuruht/q3n/releases/tag/v1.0.0`

Verify at `https://github.com/thuruht/q3n/releases` that all three assets are present.

---

## Self-Review Notes

- `.gitignore` fix is in Task 1 before any new files are created — no risk of accidentally hiding them.
- `appimagetool` is downloaded to `scripts/` but gitignored via the explicit `scripts/appimagetool-x86_64.AppImage` rule.
- `AppDir/usr/` is rebuilt fresh each run (`rm -rf "$APPDIR/usr"`) so stale PyInstaller output doesn't accumulate.
- `--dry-run` builds all three artifacts locally (real smoke test) but skips tag + upload.
- Release is created as `draft=true` first so a partial upload failure doesn't publish an incomplete release.
- `dpkg-buildpackage` outputs to `../` — the `$DEB` path in `release.sh` accounts for this.
