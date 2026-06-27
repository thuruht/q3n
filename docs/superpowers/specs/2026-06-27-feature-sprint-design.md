# Q3N Feature Sprint — Design Spec
**Date:** 2026-06-27
**Status:** Approved

## Overview

Six parallel tracks delivered as one sprint:

1. Central version
2. Schema validation
3. Browser demo
4. Meta-app framework (fully defined)
5. Fortune plugin (first plugin)
6. Citation engine plugin (second plugin, first full-featured)

Tracks 5 and 6 are built on top of Track 4. Tracks 1–3 are independent housekeeping.

---

## Track 1: Central Version

**Goal:** Single source of truth for the version string.

**Changes:**
- `core/__init__.py` — add `__version__ = "1.0.0"`
- `setup.py` — replace hardcoded `version='1.0.0'` with `from core import __version__; version=__version__`
- `tools/q3n` — import `__version__` from `core` for `--version` flag
- `gui/main_window.py` `_show_about()` — replace hardcoded `"1.0.0"` with `from core import __version__`
- `app/src/main.py` — replace hardcoded `'1.0.0'` in `app.setApplicationVersion()`

No new files. All consumers read from `core.__version__`.

---

## Track 2: Schema Validation

**Goal:** Opt-in per-entry URI validation with a CLI subcommand.

### `core/q3n.py` additions

```python
def validate_uri(uri: str) -> list[str]:
    """Return list of validation errors for uri. Empty = valid."""
```

Per-scheme rules:
- **https / http** — `urlparse(uri).netloc` must be non-empty
- **isbn** — strip hyphens/spaces; run ISBN-10 or ISBN-13 checksum algorithm
- **doi** — must match `^10\.\d{4,}/\S+`
- **arxiv** — must match `^\d{4}\.\d{4,5}(v\d+)?$` or legacy `^[a-z\-]+/\d{7}$`
- **yt** — video ID segment must be exactly 11 characters
- **q3n** — must contain at least one non-empty path segment after `q3n://`
- **file** — path segment after `file://` must be non-empty
- **Unknown scheme** — no error (pass-through)

### `Q3NEntry` addition

```python
def validate(self) -> list[str]:
    return validate_uri(self.uri)
```

### CLI addition

```
q3n validate <file>
```

Output format:
```
entry 1 (https://...): OK
entry 3 (isbn://...): invalid ISBN-13 checksum
```

Exit code 0 if all valid, 1 if any errors.

Parser remains non-strict — invalid entries still parse. Validation is always opt-in.

---

## Track 3: Browser Demo

**Goal:** Interactive live demo of the JS parser on the project website.

### New file: `docs/website/demo.html`

Self-contained page (no build step). Loads `q3n-parser.js` copied alongside it as `docs/website/q3n-parser.js` (symlink or copy; copied for simplicity).

**Layout — two-column:**
- **Left pane** — textarea pre-filled with `examples/sample.q3n` content (hardcoded string in the HTML). Label: "Paste or type Q3N text"
- **Right pane** — parsed entry cards, each showing: scheme badge (colored pill), URI (truncated), tag (if present), quote preview (first 120 chars)

**Below the columns:**
- "Export as" dropdown: JSON / Markdown / Fortune text
- Output `<pre>` block showing the formatted result

**Behaviour:**
- Re-parses on every `input` event (debounced 200ms)
- Export updates whenever the dropdown changes or entries change

**Styling:** inherits the CSS custom properties from `index.html` (copied `<style>` block, same `--primary-color` etc.)

### `docs/website/index.html` change

Add a "Try it live →" link in the hero section pointing to `demo.html`.

---

## Track 4: Meta-App Framework

**Goal:** Promote `app/` from scaffolding to a real, documented plugin system.

### Plugin protocol

A plugin is a Python package at `app/plugins/<name>/` with `__init__.py` exposing:

```python
PLUGIN_META = {
    'name': str,          # machine id, matches directory name
    'title': str,         # human display name
    'description': str,
    'version': str,
}

def register(manager: PluginManager) -> None:
    """Called once at startup."""
```

Inside `register`, the plugin calls any combination of:

```python
manager.register_panel(name, WidgetClass)
    # Adds a tab to MainWindow's plugin sidebar.
    # WidgetClass(parent) constructor; MainWindow calls set_entries(entries) after construction
    # and whenever the open file changes. set_entries() is required on all panel widgets.

manager.register_action(name, callable)
    # Registers a named callable (menu item, toolbar button, CLI action).

manager.register_standalone(name, callable)
    # callable(entries: list[Q3NEntry], args: list[str]) -> None
    # Launched via `q3n run <name> [file] [args...]`
```

### `app/src/core/plugin_manager.py` additions

```python
def register_panel(self, name: str, widget_class: type) -> None
def register_standalone(self, name: str, func: callable) -> None
def list_plugins(self) -> list[tuple[str, dict]]  # [(name, meta), ...]
def run_standalone(self, name: str, entries, args) -> None
```

Plugin discovery searches, in order:
1. `app/plugins/` (built-in plugins)
2. `~/.q3n/plugins/` (user-installed plugins)
3. `./plugins/` (project-local plugins)

### GUI integration

`gui/main_window.py` grows a **plugin sidebar** — a `QDockWidget` on the right, containing a `QTabWidget`. Each registered panel becomes a tab, labelled with `PLUGIN_META['title']`. The dock is hidden when no plugins are loaded.

When the open file changes, `MainWindow` emits a signal; each panel widget receives the new `list[Q3NEntry]` via a `set_entries(entries)` method (required on all panel widgets).

### CLI integration

`tools/q3n` gets a new `run` subcommand:

```
q3n run <plugin> [file] [-- plugin-args...]
```

This discovers plugins, finds the one named `<plugin>`, loads entries from `[file]` if given, and calls `run_standalone(entries, args)`. Prints an error if the plugin is not found or has no standalone mode.

### File layout

```
app/
  plugins/
    fortune/
      __init__.py        # register()
      panel.py           # FortunePanelWidget
      widget.py          # FortuneOverlay (moved from app/src/widgets/)
    cite/
      __init__.py        # register()
      panel.py           # CitePanelWidget
      formatter.py       # citation formatting engine
  src/
    core/
      plugin_manager.py  # extended
      ui_loader.py       # unchanged
    main.py              # updated to use PluginManager
```

---

## Track 5: Fortune Plugin

**Goal:** Convert the existing fortune widget into a proper registered plugin.

### `app/plugins/fortune/__init__.py`

```python
PLUGIN_META = {
    'name': 'fortune',
    'title': 'Fortune',
    'description': 'Random quote overlay and sidebar card.',
    'version': '1.0.0',
}

def register(manager):
    from .panel import FortunePanelWidget
    from .widget import FortuneOverlay
    manager.register_panel('fortune', FortunePanelWidget)
    manager.register_standalone('fortune', _run_standalone)

def _run_standalone(entries, args):
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    from .widget import FortuneOverlay
    w = FortuneOverlay(entries=entries)
    w.show()
    sys.exit(app.exec())
```

### `app/plugins/fortune/panel.py`

`FortunePanelWidget` — compact card shown in the MainWindow sidebar:
- Displays one random entry (quote + attribution) in a styled card
- "Next" button picks a new random entry
- "Pop out" button launches `FortuneOverlay`
- `set_entries(entries)` updates the pool

### `app/plugins/fortune/widget.py`

Move `app/src/widgets/fortune_widget.py` here, no logic changes.

### CLI alias

`q3n fortune` remains as a top-level alias for `q3n run fortune`.

---

## Track 6: Citation Engine Plugin

**Goal:** First full-featured plugin — formats Q3N entries as academic citations.

### Supported styles and schemes

| Style | isbn | doi | arxiv | https | yt | q3n |
|---|---|---|---|---|---|---|
| MLA 9 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| APA 7 | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Chicago 17 (author-date) | ✓ | ✓ | ✓ | ✓ | — | — |
| BibTeX | ✓ | ✓ | ✓ | — | — | — |

### `app/plugins/cite/formatter.py`

```python
def format_citation(entry: Q3NEntry, style: str) -> str:
    """Format entry as a citation string. style: 'mla'|'apa'|'chicago'|'bibtex'"""
```

Dispatches to `_format_<style>(entry)` → `_format_<style>_<scheme>(meta)`.

Missing metadata fields fall back gracefully:
- Missing author → `[n.a.]` (MLA/Chicago) or omitted (APA)
- Missing year → `n.d.` (APA) or `[n.d.]` (MLA/Chicago)
- Missing publisher → `[n.p.]`

All metadata comes from `entry.as_dict()['meta']` — no network calls, no external deps.

### Example outputs

**MLA 9 (isbn):**
```
Doe, Jane. *The Example Book*. Example Press, 1999.
```

**APA 7 (doi):**
```
Doe, J. (2021). Title of article. *Journal Name*. https://doi.org/10.1234/example
```

**Chicago 17 author-date (arxiv):**
```
Doe, Jane. 2021. "Paper Title." arXiv:2101.00001.
```

**BibTeX (isbn):**
```bibtex
@book{doe1999,
  author    = {Doe, Jane},
  title     = {The Example Book},
  publisher = {Example Press},
  year      = {1999},
  isbn      = {978-0-00-000000-0}
}
```

### `app/plugins/cite/panel.py`

`CitePanelWidget` (MainWindow sidebar tab):
- Entry list (synced via `set_entries`)
- Style selector: MLA / APA / Chicago / BibTeX
- Formatted citation in a read-only text box
- "Copy" button

### Standalone / CLI

```
q3n run cite <file> [--style apa] [--entry N] [--all]
q3n cite <file> [--style apa]        # alias
```

`--style` default: `apa`. `--all` prints every entry. Without `--entry` or `--all`, prints first entry.

Exit code 0 always (citation formatting never fails — it degrades gracefully).

---

## Testing

- **Track 1** — existing tests continue passing; add assertion that `Q3NEntry` version import resolves
- **Track 2** — unit tests for each scheme validator (valid + invalid cases per scheme); test that parser still accepts invalid URIs
- **Track 3** — manual browser test only (no JS test framework change needed; existing `test-q3n-parser.js` already covers the parser)
- **Track 4** — test plugin discovery, `register_panel/standalone`, `list_plugins`, CLI `run` dispatch
- **Track 5** — smoke test `_run_standalone` can be called without a display (`QApplication` headless guard)
- **Track 6** — unit tests for `format_citation` covering each style × scheme combination, including graceful degradation for missing fields

---

## Implementation Order

1. Track 1 (central version) — unblocks all other tracks that need version
2. Track 2 (schema validation) — independent, can go in parallel
3. Track 3 (browser demo) — independent
4. Track 4 (meta-app framework) — must precede Tracks 5 and 6
5. Track 5 (fortune plugin) — after Track 4
6. Track 6 (citation plugin) — after Track 4; citation formatter can be developed in parallel with Track 4
