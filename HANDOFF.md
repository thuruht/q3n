# Q3N — Handoff Document

## Session Summary

We started with a Debian-packaged Q3N project (`core/q3n.py`, `tools/q3n` CLI, `gui/`),
discovered orphaned features on the GitHub repo (fortune, extended parser, VS Code
extension, CI/CD, tests, examples), and re-incorporated everything.

### Files Created

| File | Purpose |
|---|---|
| `core/q3n.py` | Rewritten: 7 scheme-specific URI parsers (`q3n://`, `yt://`, `doi://`, `arxiv://`, `isbn://`, `file://`, `https/http`), query param/fragment extraction, `resolve_uri()` attribution, `detect()` with existence guard, JSON/MD/HTML/txt/index/fortune export |
| `core/fortune.py` | Fortune module: 8 ASCII art designs, `display_fortune()` with `box_text()`, `export_fortune()` for `strfile`-compat format |
| `tests/__init__.py` | Test package marker |
| `tests/test_q3n.py` | 50 pytest tests covering parse, serialize, roundtrip, all 7 URI scheme parsers, attribution, export formats, detection, edge cases |
| `vscode-extension/package.json` | VS Code extension manifest with `.q3n/.q3nt/.quotation/.quotes` file associations, language config, snippets |
| `vscode-extension/syntaxes/q3n.tmLanguage.json` | TextMate grammar with syntax highlighting for URIs (web, academic, media, person), tag delimiters, format header |
| `vscode-extension/language-configuration.json` | Folding markers, auto-closing pairs, word pattern |
| `vscode-extension/snippets/q3n.json` | 4 snippets: new entry, web, book, person |
| `.github/workflows/ci.yml` | GitHub Actions: flake8 lint, pytest (Python 3.9–3.12), CLI smoke test, Debian build, VS Code extension validation |
| `examples/sample.q3n` | 7 entries: web, ISBN, person, DOI, YouTube, arXiv, book |
| `examples/diverse.q3n` | 6 entries: web, dystopia, civil-rights, file, anonymous, fiction |

### Files Modified

| File | Changes |
|---|---|
| `tools/q3n` | New `cmd_fortune()` function; `fortune` subcommand registered with `--count`, `--art`, `--no-art` flags; `from core.fortune import display_fortune, export_fortune` added |
| `core/q3n.py` | Regex `\S+` → `.+?` to allow non-whitespace chars in URIs before ` /// tag:` delimiter; `detect()` now checks `p.exists()` before returning True on extension match |

### Verification

- All 3 Python files compile clean
- **50/50 pytest tests pass**
- CLI `q3n fortune examples/sample.q3n` works with attribution
- Debian package rebuilds successfully at `../q3n_1.0.0-1_all.deb` (24,968 bytes)


## Answers to Your Questions

### 1. Does the GUI use the core library?

**Yes.** 4 of 8 files in `gui/` import from `core.q3n`:

| File | What it imports |
|---|---|
| `gui/main_window.py` | `Q3NEntry, parse_file, serialize_file, export_file, export_json, export_markdown, export_plaintext, generate_index, import_json` |
| `gui/entry_view.py` | `Q3NEntry` |
| `gui/entry_dialog.py` | `Q3NEntry` |
| `gui/entry_wizard.py` | `Q3NEntry` |

The GUI currently uses `core.q3n` for: parsing Q3N files, serializing entries, exporting to various formats, and constructing entry objects. But it does **not** use any of the new derived-metadata features (attribution, scheme-specific parsing, categories).

### 2. Can the GUI reflect the new features?

**Yes.** Specifically:

- **List view** (`EntryDelegate` in `main_window.py:128`): currently shows only `quote[:80]` + `[tag]`. It could show URI preview, scheme icon, or attribution.
- **Detail view** (`EntryDetailView` in `entry_view.py:8`): currently shows URI, tag, scheme (text), quote. It could show an "Attribution" read-only field (`entry.attribution()`), a "Category" badge (`entry.as_dict()['category']`), and scheme-specific metadata (domain for web, author for ISBN, etc.).
- **Filter/search** (main_window.py:313): already searches `e.uri` and `e.quote`. Could be extended to search derived metadata too.

### 3. What about the "meta-app / app-app"?

This was referring to the AppImage launcher concept — a portable, self-contained application bundle. Currently there's no AppImage build, just:
- `gui/app.py` (simple launcher)
- `gui/__main__.py` (allows `python3 -m gui`)
- `bin/q3n-gui` (installed system-wide to `/usr/bin/q3n-gui` via the .deb)
- Debian packaging (`debian/` directory)

An AppImage would require bundling Python + PySide6 + all Q3N modules into a single executable. This is not yet implemented.

### 4. About dialog

Located at `gui/main_window.py:568` (`_show_about()`). Currently hardcodes version as `"1.0.0"`. There's no central `__version__` variable anywhere — version lives in `setup.py` only. The About dialog should ideally read from a single source of truth.


## Architectural Notes

### URI Parsing Flow

```
User enters URI in GUI or CLI
         ↓
  parse_scheme(uri) → splits "scheme://rest" into (scheme, path)
         ↓
  Q3NEntry(uri, scheme, path, quote, tag)
         ↓
  entry._derive() → dispatches to URI_PARSERS[scheme]()
         ↓
  entry.attribution() → human-readable source string
```

New scheme parsers live in `core/q3n.py` under the `URI_PARSERS` dict. Adding a new scheme requires:
1. Write a `parse_<name>_uri(uri)` function
2. Add it to `URI_PARSERS`
3. Optionally add to `SCHEME_REGISTRY` for category mapping
4. Optionally update `resolve_uri()` for attribution

### GUI Entry Flow

```
parse_file(path) → List[Q3NEntry]
         ↓
  EntryListModel wraps entries (stores Q3NEntry at Qt.UserRole)
         ↓
  QListView + EntryDelegate renders list
         ↓
  On selection → EntryDetailView.show_entry(row, entry)
         ↓
  User edits → EntryDetailView._save() → emits entry_changed(row, Q3NEntry)
         ↓
  main_window._on_entry_changed() → model.update_entry(row, entry)
```

### Version String

Currently only in `setup.py:6` (`version='1.0.0'`). There's no `__version__` in `core/__init__.py` or `core/q3n.py`. Both the CLI and GUI derive version from the Debian package or hardcode it. Recommended: add `__version__ = "1.0.0"` to `core/__init__.py` and have both CLI and GUI read it from there.


## Commands Reference

```
q3n show <file> [n]              Display entries
q3n list [dir]                    List entries across files
q3n create <file>                 Interactive entry wizard
q3n edit <file> [n]               Edit entry
q3n search <pattern> [dir]        Search entry text (regex)
q3n stats [dir]                   Collection statistics
q3n export <file> -o <path> -f fmt  Export (txt|json|md|q3n|html|index|fortune)
q3n import <src> <dest>           Import entries
q3n index [dir]                   Generate markdown index
q3n init <file>                   Create empty Q3N file
q3n fortune [dir] [-c N] [--art NAME] [--no-art]  Random fortune display
q3n tutorial                      Interactive tutorial
q3n help [command]                Show help / man page
```

## MIME Types Registered

| Extension | MIME Type |
|---|---|
| `.q3n` | `application/x-q3n` |
| `.q3nt` | `application/x-q3n` |
| `.quotation` | `application/x-q3n` |
| `.quotes` | `application/x-q3n` |

Registered in system MIME database — no conflicts with any existing freedesktop/global/local associations.

## Session 2: Re-incorporating Remaining Orphaned Features

### #1 GUI metadata display (completed)
- **`gui/entry_view.py`**: Added Attribution read-only field, Category badge (colored label), and scheme-specific metadata row (domain, author, ISBN, DOI, arXiv ID, video ID, line number, file path). Uses `entry.attribution()` and `entry.as_dict()`.
- **`gui/main_window.py`**: Updated `EntryDelegate` to show scheme icon + quote preview + attribution subtitle; increased row height to 50px.

### #1b Bugfix: parser catastrophic backtracking (completed)
- **`core/q3n.py`**: Replaced regex-based `Q3N_PATTERN.finditer()` with line-by-line parser (`lines.split('\n')`, `Q3N_START.match()`, `Q3N_END.match()`). Eliminates all backtracking — no hang on large files. Entries without closing `\\\` are silently dropped.

### #1c Bugfix: cmd_list ValueError (completed)
- **`tools/q3n`**: Wrapped `path.relative_to()` in try/except ValueError — fallback to absolute path when not a subdirectory.

### #2 Extended syntax (completed)
- **`core/q3n.py`**: Added `detect_content_type(quote)` — classifies quote bodies as `'text'`, `'json'`, or `'code'` (heuristic: JSON parse test, code keyword ratio, fence detection). Added `content_type` to `Q3NEntry._derive()` output.
- **`examples/extended.q3n`**: 9-entry example with URI query params (`?lang=en`, `?src=paper&page=42`), fragment IDs (`#section-3`), JSON-structured quote body, Python code quote body, yt:// timestamps.
- **Tests**: 13 new tests (50 → 63 total) covering content type detection, JSON entry parse, code entry parse, extended syntax roundtrip.

### #3 Fortune shell wrappers (completed)
- **`scripts/fortune-q3n.sh`**: Shell wrapper calling `q3n fortune`. Drop-in replacement for `fortune` command on Q3N collections.
- **`scripts/q3n-strfile.sh`**: Converts Q3N file to strfile(8)-compatible format for use with standard `fortune` command.
- **`art/ascii-art.txt`**: 9 ASCII art designs in a documented reference format.

### #4 JavaScript parser (completed)
- **`src/js/q3n-parser.js`**: Full port (466 lines) mirroring Python API: `parse()`, `serialize()`, `detect()`, `detectContentType()`, `Q3NEntry`, `URI_PARSERS` (8 schemes), `exportJson()`, `exportMarkdown()`, `exportFortune()`, `displayFortune()`. Auto-wired CLI with `extract`, `validate`, `json`, `fortune` commands. Works in Node.js and browser.
- **`src/js/test-q3n-parser.js`**: 22 tests covering parse, URI parsing, content type, attribution, detection, serialization, exports, fortune.
- **Tests**: 22/22 pass.

### #5 Qt6 Meta-Application Framework (completed)
- **`app/src/main.py`**: Entry point supporting `--fortune`, `--designer`, `--list-ui` modes.
- **`app/src/core/ui_loader.py`**: Runtime `.ui` file loader with `SignalRouter` — auto-wires signals to handlers via naming convention (`on_{objectName}_{signalName}`). Discovers UI files in multiple search paths.
- **`app/src/core/plugin_manager.py`**: Plugin discovery from `app/plugins/`. Supports `register_action()`, `register_widget()`, `register_hook()` with dispatch.
- **`app/src/widgets/fortune_widget.py`**: `FortuneOverlay` — frameless, stay-on-top desktop widget. Configurable interval (10s–30min), opacity (30–100%), click-through mode, category filtering, drag-to-move.
- **`app/src/meta_app_main.py`**: Standalone app generator — copies template structure with `q3n-app.json` manifest.
- **`app/resources/ui/main_window.ui`**: Example Qt Designer UI file to demonstrate designer-ready mode.
- **`app/templates/default/`**: Default meta-app template structure with manifest.

### CI update
- **`.github/workflows/ci.yml`**: Added `fortune` shell script syntax check, JavaScript tests job (Node.js 20).

### Final state
- **Python tests**: 63/63 pass
- **JavaScript tests**: 22/22 pass
- **Debian package**: rebuilds successfully
- **CLI**: `q3n list` completes instantly (no hang)
- **GUI**: shows attribution with scheme icons, colored category badges, scheme-specific metadata
- **JS CLI**: `node src/js/q3n-parser.js {extract,validate,json,fortune}` works

## Known Gaps

1. **Central version**: Add `__version__` to `core/__init__.py` and reference from CLI/GUI
2. **AppImage**: Package into portable self-contained bundle
3. **Schema validation**: Add URI validation for each scheme parser
4. **i18n**: No localization support yet
5. **Python 3.13+**: `pyproject.toml` classifiers should be updated
6. **Debian dependency `python3-pyside6.qtwidgets`**: Verify on fresh installs
7. **Browser demo**: HTML page using Q3NParser in browser context
8. **Fortune plugin**: Write a sample plugin demonstrating the plugin system
