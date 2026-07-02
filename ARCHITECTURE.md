# Architecture

## Overview

```
tools/q3n          CLI entry point
bin/q3n-gui        GUI launcher
core/              Python library (no GUI deps)
  q3n.py            Q3NEntry, parse, serialize, export, validate_uri
  fortune.py        Fortune cookie renderer and ASCII art
  __init__.py       __version__
gui/               PySide6 GUI application
  __main__.py       Installed entry point
  app.py            Repo entry point (loads plugins on startup)
  main_window.py    MainWindow — file ops, menus, plugin dock, URI validation
  entry_model.py    EntryListModel (QAbstractListModel)
  entry_view.py     EntryDetailView — edit panel with inline URI validation
  entry_wizard.py   EntryWizard (multi-page new-entry wizard)
  __init__.py
app/               Plugin framework and standalone plugins
  src/core/
    plugin_manager.py  PluginManager — register/discover/run panels & standalones
    ui_loader.py       UILoader for .ui files
  plugins/
    fortune/           Fortune plugin
      __init__.py      PLUGIN_META + register(manager)
      panel.py         FortunePanelWidget (sidebar card)
      widget.py        FortuneOverlay (floating desktop widget)
    cite/              Citation plugin
      __init__.py      PLUGIN_META + register(manager)
      panel.py         CitePanelWidget (sidebar tab with style picker)
      formatter.py     format_citation(entry, style) — MLA/APA/Chicago/BibTeX
src/js/            JavaScript implementation
  q3n-parser.js     Browser + Node.js parser (window.Q3NParser)
  test-q3n-parser.js JS test suite (35 tests)
web/               Cloudflare Worker download site (Vite + React)
  public/demo.html  Interactive browser demo
  public/q3n-parser.js  JS parser for browser use
vscode-extension/  VS Code syntax highlighting extension
debian/            Debian source package layout
scripts/           Build scripts (release.sh, build-appimage.sh)
docs/
  format/specification.md  Q3N format specification
  man/q3n.1         Man page
```

## Core library (`core/q3n.py`)

### Q3NEntry

```python
Q3NEntry(uri, scheme, path, quote, tag=None)
```

- `uri` — full source URI
- `scheme` — e.g. `https`, `file`, `isbn`, `osm`, `geo`
- `path` — scheme-specific path component
- `quote` — the quoted text
- `tag` — optional slash-hierarchy tag

`as_dict()` returns a dict with derived metadata (`meta`, `category`, `content_type`).

`validate()` delegates to `validate_uri(self.uri)` — returns a list of error strings.

### parse(text) → list[Q3NEntry]

Line-by-line parser (no backtracking). Matches opening lines with a compiled regex (`Q3N_START`), collects content until a closing `\\\` line (`Q3N_END`). Entries without a closing marker are silently dropped. Parser is non-strict — invalid URIs still parse; validation is always opt-in.

### serialize(entries, header=True) → str

Reconstructs Q3N text from entry objects. `parse(serialize(entries))` is a guaranteed roundtrip.

### validate_uri(uri) → list[str]

Per-scheme validation. Empty list means valid. Checks:
- `https`/`http` — netloc present
- `isbn` — ISBN-10 or ISBN-13 checksum
- `doi` — `10.XXXX/...` format
- `arxiv` — new-style `YYMM.NNNNN` or legacy `cat/NNNNNNN`
- `yt` — video ID is exactly 11 chars
- `q3n` — non-empty path
- `file` — non-empty path
- Unknown schemes pass through without error

### Export pipelines

```
export_file(entries, path, fmt='q3n')
  fmt: q3n | json | md | html | txt | index | fortune
```

Each format has a dedicated function:
- `export_json` — JSON array
- `export_markdown` — blockquote-formatted Markdown (map/web URIs resolve to real URLs)
- `export_html` — self-contained HTML page (map/web URIs resolve to real URLs)
- `export_plaintext` — flat text
- `generate_index` — markdown table with tag summaries
- `export_fortune` (in `core/fortune.py`) — Unix fortune/strfile-compatible format

### URI parsers

URI parsing is scheme-dispatched via `URI_PARSERS` dict. Each scheme returns a `meta` dict:

| Scheme | Key metadata fields |
|--------|-------------------|
| `https`/`http` | `domain` |
| `isbn` | `isbn`, `title`, `author`, `year`, `publisher` |
| `doi` | `doi` |
| `arxiv` | `arxiv_id` |
| `pubmed` | `pmid` |
| `yt` | `video_id` |
| `spotify` | `kind`, `id` |
| `orcid` | `orcid` |
| `q3n` | `handle`, `email`, `name` |
| `file` | `path`, `line` |
| `osm` | `type`, `id`, `browse_url`, `api_url` |
| `geo` | `lat`, `lon`, `zoom`, `map_url` |
| `overpass` | `query`, `api_url` |
| `wikipedia` | `article`, `lang`, `browse_url` |
| `github` | `owner`, `repo`, `kind`, `id`, `label`, `browse_url` |

### Detection & discovery

```
detect(path) → bool        # Check if file is Q3N (extension first, then content up to 1MB)
list_entries(directory)    # Recursively discover Q3N files by extension only (fast)
```

## CLI (`tools/q3n`)

Argparse-based dispatcher. Each subcommand is a `cmd_*` function returning an exit code.
Color/icon output is gated on `sys.stdout.isatty()`. ASCII banner shown on bare invocation.

Subcommands: `show`, `list`, `create`, `edit`, `search`, `stats`, `export`, `import`,
`index`, `init`, `fortune`, `validate`, `cite`, `run`, `config`, `tutorial`, `help`

- `validate FILE` — per-entry URI validation, exits 1 if any fail
- `cite FILE [--style mla|apa|chicago|bibtex] [--entry N] [--all]` — citation formatting
- `run PLUGIN [FILE] [args...]` — runs a plugin's standalone function
- `fortune [DIR]` — random entry as ASCII art fortune cookie

`_find_app_root()` checks both the source tree and `/usr/lib/q3n/` so plugin subcommands
work whether running from the repo or from an installed package.

## Plugin framework (`app/`)

### PluginManager (`app/src/core/plugin_manager.py`)

Discovers and loads plugin packages from configured directories.

```python
pm = PluginManager()
pm.discover()                          # imports plugins from app/plugins/
pm.register_panel(name, widget_class)  # adds a sidebar tab
pm.register_standalone(name, func)     # func(entries, args) -> None
pm.run_standalone(name, entries, args) # raises KeyError if not found
pm.list_plugins()                      # [(name, PLUGIN_META), ...]
pm.panels                              # dict[str, type]
```

Each plugin module must export `PLUGIN_META` (dict) and `register(manager)`.

### Built-in plugins

**fortune** (`app/plugins/fortune/`):
- `FortunePanelWidget` — compact sidebar card; Next/Pop-out buttons
- `FortuneOverlay` — always-on-top floating widget with timer and settings
- Standalone: launches `FortuneOverlay` with loaded entries

**cite** (`app/plugins/cite/`):
- `CitePanelWidget` — style picker + entry list + citation text box + clipboard copy
- `format_citation(entry, style)` — MLA 9, APA 7, Chicago 17, BibTeX
- Standalone: `q3n run cite FILE [--style ...] [--entry N] [--all]`

**anki** (`app/plugins/anki/`):
- `AnkiPanelWidget` — sidebar tab; CSV preview + "Export CSV..." button
- `export_anki_csv(entries)` — CSV with columns Quote, Source, Tag, URI
- Standalone: `q3n run anki FILE [-o output.csv]`
- Also registered as `anki` export format in `export_file()` and `q3n export -f anki`

## GUI (`gui/`)

Built on PySide6. Architecture follows Model-View pattern.

### MainWindow (QMainWindow)

- Horizontal QSplitter: list panel (left) + detail editor (right)
- Right-side `QDockWidget` with `QTabWidget` for plugin panels (populated by `load_plugins`)
- TagFilterCombo + search QLineEdit for filtering
- QListView with EntryListModel backing
- EntryDetailView for editing selected entry
- `_notify_plugins(entries)` — pushes entry list to all loaded panel widgets on file load/edit
- `_validate_file()` — validates all URIs in current file, shows summary dialog
- File menu: New, Open, Save, Save As, Quit
- Import menu: Q3N, JSON, Plain Text
- Export menu: Q3N, JSON, Markdown, HTML, Plain Text, Index, Fortune
- Tools menu: previews, index generation, Validate URIs
- Help menu: About dialogs

Plugin dock is populated at startup via `gui/app.py`:

```python
app_root = _find_app_root()   # checks repo root and /usr/lib/q3n/
pm = PluginManager()
pm.discover()
win.load_plugins(pm)
```

### EntryListModel (QAbstractListModel)

In-memory model wrapping a `list[Q3NEntry]`. Supports:
- `set_entries`, `add_entry`, `update_entry`, `remove_entry`
- `Qt.UserRole` returns the Q3NEntry object

### EntryDetailView (QWidget)

Edit panel with URI, tag, and quote fields. Features:
- Inline URI validation label (✓ valid / ⚠ error) updated on every keystroke
- "Open ↗" button resolves map/web URIs to real browser URLs
- Scheme badge, category colour chip, and metadata display
- Emits `entry_changed(row, entry)` on save

### EntryWizard (QWizard)

Multi-page wizard:
1. SourceTypePage — pick URI scheme (includes osm/geo/overpass)
2. SourceDetailsPage — enter source identifier
3. TagPage — choose or type a tag
4. ContentPage — enter quoted text
5. ReviewPage — preview the formatted entry

## JavaScript implementation (`src/js/q3n-parser.js`)

Parallel JS port with identical format semantics. Works in Node.js and browser (`window.Q3NParser`).

```js
Q3NParser.parse(text)          // → [{uri, scheme, path, quote, tag, meta}, ...]
Q3NParser.exportJson(entries, indent)
Q3NParser.exportMarkdown(entries)
Q3NParser.exportFortune(entries)
```

Supports all URI schemes including `pubmed`, `orcid`, `spotify`, `osm`, `geo`, `overpass`, `wikipedia`, `github`.

## Debian packaging

- `debian/rules` uses `dh $@ --with python3 --buildsystem=pybuild`
- Installs `core/` and `gui/` to `/usr/lib/python3/dist-packages/`
- Installs `app/` plugin tree to `/usr/lib/q3n/` (enables `q3n run` and `q3n cite` outside source tree)
- Installs `tools/q3n` and `bin/q3n-gui` to `/usr/bin/`
- Installs `q3n.desktop` and icon to standard XDG paths
- Depends on `python3-pyside6` for GUI
