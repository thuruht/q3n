# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Q3N** (Quote Triple-Slash Notation) is a plain-text format and toolchain for storing quotations with source URIs. The format uses `/// <uri>` to open a block, quoted text in the middle, and `\\\` to close it.

## Commands

```bash
# Run tests
pytest tests/ -v --tb=short

# Run a single test
pytest tests/test_q3n.py::test_parse_web_entry -v

# Lint (matches CI)
flake8 core/ tools/ tests/ app/plugins/ gui/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 core/ tools/ tests/ app/plugins/ gui/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

# Run CLI without installing
python tools/q3n --help
python tools/q3n show examples/sample.q3n

# Run GUI without installing
python gui/app.py

# Install in editable/development mode
pip install -e .

# Run JS parser tests
node src/js/test-q3n-parser.js

# Build Debian package
dpkg-buildpackage -us -uc -b
```

## Architecture

### Core library (`core/q3n.py`)

The entire format engine lives here — no GUI dependencies. Key types and functions:

- **`Q3NEntry(uri, scheme, path, quote, tag=None)`** — the data object for one block. `as_dict()` adds derived metadata (`meta`, `category`, `content_type`). `validate()` delegates to `validate_uri(self.uri)`.
- **`parse(text) → list[Q3NEntry]`** — line-by-line parser; entries without a closing `\\\` are silently dropped. Parser is non-strict — invalid URIs still parse.
- **`serialize(entries, header=True) → str`** — inverse of `parse`; `parse(serialize(entries))` is a guaranteed roundtrip.
- **`export_file(entries, path, fmt)`** — dispatcher for all export formats (`q3n`, `json`, `md`, `html`, `txt`, `index`, `fortune`, `anki`).
- **`validate_uri(uri) → list[str]`** — per-scheme validation; empty list means valid. Checks https/http host, ISBN checksum, DOI format, arXiv ID, YouTube video ID length, q3n/file path presence. Unknown schemes pass through.
- **`detect(path) → bool`** — identifies Q3N files by extension first, then content (capped at 1MB). Used for single-file detection.
- **`list_entries(directory)`** — recursively discovers Q3N files by extension only (fast; no content scanning of unrecognized files).

URI parsing is scheme-dispatched via `URI_PARSERS` dict; schemes: `https`, `http`, `isbn`, `q3n`, `doi`, `arxiv`, `yt`, `file`, `pubmed`, `orcid`, `spotify`, `osm`, `geo`, `overpass`. Each returns a `meta` dict.

### CLI (`tools/q3n`)

Argparse dispatcher. Each subcommand is a `cmd_*` function returning an exit code. Color/icon output is gated on `sys.stdout.isatty()`. ASCII banner shown on bare invocation. `_find_app_root()` checks both the repo root and `/usr/lib/q3n/` so plugin subcommands work whether running from the repo or from an installed package.

Subcommands: `show`, `list`, `create`, `edit`, `search`, `stats`, `export`, `import`, `index`, `init`, `fortune`, `validate`, `cite`, `run`, `config`, `tutorial`, `help`

### Plugin framework (`app/`)

`app/src/core/plugin_manager.py` — `PluginManager` discovers plugin packages and exposes `register_panel`, `register_standalone`, `list_plugins`, `run_standalone`, and `panels` property.

Plugins live under `app/plugins/` and export `PLUGIN_META` (dict) and `register(manager)`:
- `app/plugins/fortune/` — `FortunePanelWidget` (sidebar card), `FortuneOverlay` (floating widget)
- `app/plugins/cite/` — `CitePanelWidget` (sidebar tab), `format_citation(entry, style)` (MLA/APA/Chicago/BibTeX)
- `app/plugins/anki/` — `export_anki_csv(entries)` (Anki-compatible CSV); standalone via `q3n run anki`

Installed to `/usr/lib/q3n/` by the Debian package.

### GUI (`gui/`)

PySide6 Model-View app. `gui/app.py` is the repo entry point; `gui/__main__.py` is the installed entry point. Both call the same `main()`, which also discovers and loads plugins via `PluginManager` on startup.

Key GUI components:
- `MainWindow` — QSplitter with list (left) + edit panel (right) + plugin dock (right, `QDockWidget`/`QTabWidget`). `_notify_plugins(entries)` pushes entries to all panel widgets on file load/edit. `_validate_file()` shows a URI validation report dialog.
- `EntryListModel` — in-memory `QAbstractListModel` wrapping `list[Q3NEntry]`
- `EntryDetailView` — edit panel with inline URI validation label (✓ / ⚠), "Open ↗" button, scheme/category badges, metadata display. Emits `entry_changed(row, entry)` signal.
- `EntryWizard` — 5-page QWizard for new entries (scheme → URI → tag → content → review); includes osm/geo/overpass source types

### JavaScript implementation (`src/js/q3n-parser.js`)

A parallel JS port of the core library with identical format semantics. Works in both Node.js (CLI: `extract`, `validate`, `json`, `fortune`) and browser (`window.Q3NParser`). Supports all URI schemes including `osm`, `geo`, `overpass`.

### Fortune integration (`core/fortune.py`)

Renders a random entry as an ASCII art fortune cookie. `display_fortune(entries)` picks art based on URI scheme heuristics. Export format (`export_fortune`) is compatible with the Unix `fortune`/`strfile` toolchain.

## Format specification

```
#!q3n-format          ← optional file header

/// https://example.com/article /// cite/article:
Quoted text here.
Multiple lines OK.
\\\

/// isbn://978-0-13-468599-1;Title;Author;1999
No tag is fine too.
\\\
```

- Tag syntax: `/// <tag>:` — slash hierarchy allowed (`note/idea`, `cite/book`)
- URI schemes with structured payloads use `;` as field separator (isbn, q3n, yt)
- Recognized file extensions: `.q3n`, `.q3nt`, `.quotation`, `.quotes`
- `geo:` uses colon-only syntax (no `//`): `geo:51.5074,-0.1278?z=13`

## Testing conventions

Tests live in `tests/` and import directly from `core/` and `app/` (no mocking, no fixtures beyond `tmp_path`).

| File | What it covers |
|------|----------------|
| `tests/test_q3n.py` | Core parser, serializer, URI parsers, export formats; `SAMPLE` constant is the canonical multi-scheme fixture |
| `tests/test_validate.py` | `validate_uri()` and `Q3NEntry.validate()` per-scheme rules |
| `tests/test_cite.py` | `format_citation()` across MLA/APA/Chicago/BibTeX and graceful degradation |
| `tests/test_plugin_manager.py` | `PluginManager` panel/standalone registration and dispatch |
| `tests/test_osm.py` | OSM/GIS URI parsers (`osm://`, `geo:`, `overpass://`) |
| `debian/tests/test_core.py` | Smoke test run during Debian package build |

## CI

GitHub Actions runs on Python 3.9–3.12: flake8 lint → pytest → CLI smoke test → shell script syntax check → Debian package build. A separate job validates the VS Code extension JSON and runs the JS parser tests with Node 20.

## Code review checklist — read this before every change

These are anti-patterns discovered in a project-wide audit. Check each before committing.

### Scheme tables must stay in sync

Scheme data lives in **5 locations** — adding or removing a scheme requires touching all:
- `core/q3n.py` — `SCHEME_REGISTRY` + `URI_PARSERS`
- `tools/q3n` — `SCHEME_COLORS` + `SCHEME_ICONS` + wizard scheme list + URI help text
- `gui/entry_view.py` — `SCHEME_ICONS`
- `gui/main_window.py` — `SCHEME_DISPLAY_ICONS`
- Missing schemes cause silent failures (missing badge, missing icon, wrong color)

If you add a scheme, grep for `SCHEME_ICONS`, `SCHEME_COLORS`, `SCHEME_DISPLAY_ICONS`, `SCHEME_REGISTRY`, and `URI_PARSERS` to find every location.

### CLI `cmd_*` must handle every argparse choice

If `add_argument('--format', choices=['a','b','c','d'])` lists N choices, the handler must implement all N. The most common bug is adding a choice but forgetting the handler — argparse accepts it silently, then the user gets `"Unknown format"` at runtime.

**Rule:** When adding an argparse `choices` value, write the handler case first, then add the choice. Better yet, delegate to `core.q3n.export_file()` which handles all formats automatically.

### Qt dirty-flag pattern

```python
# WRONG — setText triggers textChanged → _mark_dirty sets _dirty = True
self._dirty = False
self._uri_input.setText(entry.uri)

# RIGHT — block signals during population
self._uri_input.blockSignals(True)
self._uri_input.setText(entry.uri)
self._uri_input.blockSignals(False)
self._dirty = False
```

### Never `except Exception: pass`

Bare `except Exception: pass` hides `KeyboardInterrupt`, `MemoryError`, and genuine bugs. Always narrow to expected exception types:

```python
# WRONG
except Exception:
    pass

# RIGHT
except (OSError, ValueError):
    pass
```

Exception: `open_path` in `gui/` may legitimately catch broad exceptions, but must show an error dialog (not silent pass).

### Export dispatch must not duplicate core logic

`cmd_export` in `tools/q3n` should call `core.q3n.export_file()`. Do not write your own if/elif chain — it will inevitably miss formats that `export_file` already handles.

### JS and Python must stay in parity

The JS parser (`src/js/q3n-parser.js`) should support every URI scheme the Python parser does. Currently the JS parser is missing `osm://`, `geo:`, `overpass://`. Before claiming JS supports a scheme in docs, implement it.

There are **two identical copies** of the JS parser: `src/js/q3n-parser.js` and `web/public/q3n-parser.js`. Fix both, or symlink one to the other.

### `setup.py` must include all packages

`find_packages()` includes subdirectories with `__init__.py`. If you exclude `app/`, users who `pip install q3n` get no plugins — `q3n run` and `q3n cite` silently break. When adding a new Python package directory, check `setup.py` includes it.

### `ConfigParser` always needs `interpolation=None`

```python
# WRONG — % in config values crashes with InterpolationError
cfg = configparser.ConfigParser()

# RIGHT
cfg = configparser.ConfigParser(interpolation=None)
```

### Build dependencies must be tracked in git

If a file is in `.gitignore` and also referenced by `debian/rules` or a build script, the build breaks on a fresh clone. Before referencing a file in packaging, `git add` it first.

### Dead code must be removed

If you write a class or function and don't import it anywhere (e.g. `gui/entry_dialog.py`), remove it. Dead code is not harmless — it wastes reader attention and can become stale reference for AI agents that assume it's in use.

### Every file in a list of values must be real

When you document "7 export formats" or "14 URI schemes", every item in that list must exist in the code. If you write documentation for a feature that doesn't exist yet, you create a documentation-integrity debt that will be found later.

### Version numbers must be bumped everywhere

When bumping `__version__` in `core/__init__.py`:
- `docs/man/q3n.1` — header `.TH` line
- `docs/format/specification.md` — title line
- `q3n.appdata.xml` — `<release>` element
- `debian/changelog` — new entry
- Git tag — `vX.Y.Z`
- Search for any other file mentioning the old version string

### Man page must list all options

When adding an argparse flag (e.g. `--count` to `fortune`), add it to `docs/man/q3n.1` in the same commit. The man page is the canonical reference for installed users who don't have `--help`.

### CI scope must match documented scope

If `CLAUDE.md` says CI lints `app/plugins/` and `gui/`, the CI workflow must actually lint those directories. Out-of-date docs cause blind spots where CI misses problems in those directories.

### CLI `help` subcommand must not be a no-op

If `q3n help <subcommand>` exists, it should show help for that subcommand — not silently fall through to the generic listing. Either implement per-command dispatch or remove the `<command_name>` argument.
