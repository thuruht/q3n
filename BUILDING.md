# Building Q3N

## Requirements

- Python 3.9+
- PySide6 6.5+ (for GUI)
- setuptools (for pip install)

## From source

```bash
# Editable install (development)
pip install -e .

# Regular install
pip install .
```

## Running without install

```bash
./tools/q3n           # CLI
./bin/q3n-gui         # GUI
```

## Debian package (`.deb`)

Uses dh-python with debhelper-compat (= 13).

```bash
# Install build dependencies
sudo apt-get install -y debhelper-compat dh-python python3-all python3-setuptools

# Build the package
dpkg-buildpackage -us -uc -b

# Or with debuild
debuild -us -uc -b
```

The package installs to `/usr/bin/q3n` and `/usr/bin/q3n-gui` with Python packages at `/usr/lib/python3/dist-packages/`.

## AppImage

Uses PyInstaller with a preconfigured spec file.

```bash
# Install PyInstaller
pip install pyinstaller

# Build the AppImage
bash scripts/build-appimage.sh <version>
```

The spec file at `scripts/q3n.spec` freezes the GUI app along with the `core/`,
`gui/`, `app/`, `art/`, and `examples/` directories. The build script assembles
an AppDir and packages it with `appimagetool`, producing a standalone executable
in `build/q3n-<version>.AppImage`.

## Verifying

```bash
python3 -c "
from core.q3n import parse, serialize, Q3NEntry
text = '/// https://x.com /// t:\\nhello\\\\\\'
e = parse(text)
assert len(e) == 1
assert e[0].uri == 'https://x.com'
print('Core tests passed')
"
```
