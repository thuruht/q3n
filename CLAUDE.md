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
flake8 core/ tools/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 core/ tools/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

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

- **`Q3NEntry(uri, scheme, path, quote, tag=None)`** — the data object for one block. `as_dict()` adds derived metadata (`meta`, `category`, `content_type`).
- **`parse(text) → list[Q3NEntry]`** — line-by-line parser; entries without a closing `\\\` are silently dropped.
- **`serialize(entries, header=True) → str`** — inverse of `parse`; `parse(serialize(entries))` is a guaranteed roundtrip.
- **`export_file(entries, path, fmt)`** — dispatcher for all export formats (`q3n`, `json`, `md`, `html`, `txt`, `index`, `fortune`).
- **`detect(path) → bool`** — identifies Q3N files by extension, `#!q3n-format` header, or content pattern.
- **`list_entries(directory)`** — recursively discovers and parses Q3N files.

URI parsing is scheme-dispatched via `URI_PARSERS` dict; each scheme (`https`, `http`, `isbn`, `q3n`, `doi`, `arxiv`, `yt`, `file`, `pubmed`, `orcid`, `spotify`, `osm`, `geo`, `overpass`) has its own parser function returning a `meta` dict.

### CLI (`tools/q3n`)

Argparse dispatcher. Each subcommand is a `cmd_*` function returning an exit code. Color/icon output is gated on `sys.stdout.isatty()`. The script adds the repo root to `sys.path` at startup so it works without installation.

### GUI (`gui/`)

PySide6 Model-View app. `gui/app.py` is the repo entry point; `gui/__main__.py` is the installed entry point. Both just call the same `main()`. The GUI layers on top of `core/` with no shared state — it reads/writes files through `parse_file` and `serialize_file`.

Key GUI components:
- `MainWindow` — QSplitter with list (left) + edit panel (right), file/import/export menus
- `EntryListModel` — in-memory `QAbstractListModel` wrapping `list[Q3NEntry]`
- `EntryDetailView` — edit panel, emits `entry_changed(row, entry)` signal
- `EntryWizard` — 5-page QWizard for new entries (scheme → URI → tag → content → review)

### JavaScript implementation (`src/js/q3n-parser.js`)

A parallel JS port of the core library with identical format semantics. Works in both Node.js (CLI: `extract`, `validate`, `json`, `fortune`) and browser (`window.Q3NParser`). The JS parser does not support the `\\\` at end-of-line variant that the Python parser handles.

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

## Testing conventions

Tests live in `tests/test_q3n.py` and import directly from `core/` (no mocking, no fixtures beyond `tmp_path`). The `SAMPLE` constant at the top of the test file is the canonical multi-scheme fixture used across many tests. Debian packaging also includes `debian/tests/test_core.py`.

## CI

GitHub Actions runs on Python 3.9–3.12: flake8 lint → pytest → CLI smoke test → shell script syntax check → Debian package build. A separate job validates the VS Code extension JSON and runs the JS parser tests with Node 20.
