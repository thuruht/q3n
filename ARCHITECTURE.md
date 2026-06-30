# Architecture

## Overview

```
tools/q3n          CLI entry point
bin/q3n-gui        GUI launcher
core/              Python library (no GUI deps)
  q3n.py            Q3NEntry, parse, serialize, export, import
  fortune.py        Fortune cookie renderer and ASCII art
  __init__.py
gui/               PySide6 GUI application
  __main__.py       Installed entry point
  app.py            Repo entry point
  main_window.py    MainWindow, TagFilterCombo, PreviewDialog
  entry_model.py    EntryListModel (QAbstractListModel)
  entry_view.py     EntryDetailView (edit panel)
  entry_dialog.py   EntryDialog (quick add/edit)
  entry_wizard.py   EntryWizard (multi-page new-entry wizard)
  __init__.py
```

## Core library (`core/q3n.py`)

### Q3NEntry

```python
Q3NEntry(uri, scheme, path, quote, tag=None)
```

- `uri` — full source URI
- `scheme` — e.g. `https`, `file`, `isbn`
- `path` — scheme-specific path component
- `quote` — the quoted text
- `tag` — optional slash-hierarchy tag

`as_dict()` returns a dict with derived metadata (domain, ISBN details, etc.).

### parse(text) → list[Q3NEntry]

Line-by-line parser (no backtracking). Matches opening lines with a compiled regex (`Q3N_START`), collects content until a closing `\\\` line (`Q3N_END`). Entries without a closing marker are silently dropped.

```
/// <uri> [/// <tag>:]
<content>
\\\      (triple backslash on its own line)
```

### serialize(entries, header=True) → str

Reconstructs Q3N text from entry objects.

### Export pipelines

```
export_file(entries, path, fmt='q3n')
  fmt: q3n | json | md | html | txt | index | fortune
```

Each format has a dedicated function:
- `export_json` — JSON array
- `export_markdown` — blockquote-formatted Markdown
- `export_html` — self-contained HTML page
- `export_plaintext` — flat text
- `generate_index` — markdown table with tag summaries
- `export_fortune` (in `core/fortune.py`) — Unix fortune/strfile-compatible format

### Detection & discovery

```
detect(path) → bool        # Check if file is Q3N (by extension, header, or content)
list_entries(directory)    # Recursively discover Q3N files
```

## CLI (`tools/q3n`)

Argparse-based dispatcher. Each subcommand is a `cmd_*` function returning an exit code.

- `help [command]` — delegates to man page or prints command list
- `tutorial` — interactive text tutorial with sections and prompts
- `fortune` — display random entry as ASCII art fortune cookie
- `validate` — check URIs against per-scheme rules; exits 1 on any failure
- `cite [--style mla|apa|chicago|bibtex]` — format entries as citations via `app/plugins/cite`
- `run <plugin> [file]` — launch a plugin standalone via `PluginManager`
- `show`, `list`, `create`, `edit`, `search`, `stats`, `export`, `import`, `index`, `init`

## GUI (`gui/`)

Built on PySide6 (Qt for Python). Architecture follows Model-View pattern.

### MainWindow (QMainWindow)

- Horizontal QSplitter: list panel (left) + detail editor (right)
- TagFilterCombo + search QLineEdit for filtering
- QListView with EntryListModel backing
- EntryDetailView for editing selected entry
- File menu: New, Open, Save, Save As, Quit
- Import menu: Q3N, JSON, Plain Text
- Export menu: Q3N, JSON, Markdown, HTML, Plain Text, Index
- Tools menu: previews + index generation
- Help menu: About dialogs

### EntryListModel (QAbstractListModel)

In-memory model wrapping a `list[Q3NEntry]`. Supports:
- `set_entries`, `add_entry`, `update_entry`, `remove_entry`
- Qt.UserRole returns the Q3NEntry object

### EntryDetailView (QWidget)

Edit panel with URI, tag, and quote fields. Emits `entry_changed(row, entry)`.

### EntryWizard (QWizard)

Multi-page wizard:
1. SourceTypePage — pick URI scheme
2. SourceDetailsPage — enter source identifier
3. TagPage — choose or type a tag
4. ContentPage — enter quoted text
5. ReviewPage — preview the formatted entry

## Plugin system (`app/`)

Plugins extend the CLI and GUI without touching core code.

```
app/
  plugins/
    fortune/    FortunePanelWidget (sidebar card) + FortuneOverlay (standalone window)
    cite/       CitePanelWidget + format_citation(entry, style) engine
  src/
    core/plugin_manager.py    PluginManager — register_panel, register_standalone, run_standalone
    main.py                   Meta-app entry point (loads plugins into GUI dock)
```

The GUI's `MainWindow.load_plugins(manager)` creates a right-side `QDockWidget` with one tab per
registered panel. `q3n run <plugin>` invokes `run_standalone` from the CLI. The plugin directory
is installed to `/usr/lib/q3n/app/` by the Debian package and must be in `PYTHONPATH` or sys.path
for the CLI to find it outside the source tree.

## Debian packaging

- `debian/` — standard Debian source package layout
- `debian/rules` uses `dh $@ --with python3 --buildsystem=pybuild`; also installs `app/` Python
  files to `/usr/lib/q3n/app/` and the icon to `/usr/share/pixmaps/q3n.png`
- Depends on `python3-pyside6.qtwidgets` for GUI
- Build-Depends on `debhelper-compat (= 13)`, `dh-python`, `python3-all`, `python3-setuptools`
