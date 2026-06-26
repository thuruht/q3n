# Building Q3N

## Requirements

- Python 3.8+
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

Two approaches:

### Option A: pyside6-deploy (Nuitka-based)

```bash
pip install pyside6-deploy
pyside6-deploy gui/__main__.py --name Q3N-Manager
```

### Option B: pyproject-appimage

```bash
pip install pyproject-appimage
pyproject-appimage build
```

Both produce a standalone executable in `dist/`.

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
