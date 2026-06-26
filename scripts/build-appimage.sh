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
