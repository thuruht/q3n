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

if [ "$DRY_RUN" = false ]; then
    : "${GITHUB_TOKEN:?GITHUB_TOKEN env var is required}"
fi

echo "==> Q3N Release v${VERSION}$([ "$DRY_RUN" = true ] && echo ' (DRY RUN)' || true)"

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

# 2. Build .deb first (its clean step wipes build/dist and build/work)
echo "==> Building Debian package..."
cd "$REPO_ROOT"
dpkg-buildpackage -us -uc -b
if [ ! -f "$DEB" ]; then
    echo "ERROR: Expected .deb not found at $DEB" >&2
    exit 1
fi

# 3. Build AppImage (after deb clean has already run)
echo "==> Building AppImage..."
"$REPO_ROOT/scripts/build-appimage.sh" "$VERSION"
if [ ! -f "$APPIMAGE" ]; then
    echo "ERROR: Expected AppImage not found at $APPIMAGE" >&2
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
