# Q3N Sprint Handoff — 2026-06-27

## Sprint Plan
`docs/superpowers/plans/2026-06-27-feature-sprint.md`

## Completed Tasks

| # | Task | Commit(s) |
|---|------|-----------|
| 1 | Central version + Python classifiers | `e895d08` |
| 2 | Schema validation (`validate_uri`, `Q3NEntry.validate`) | `94141e8` |
| 3 | `q3n validate` CLI subcommand | `69e4bb1` |
| 4 | Browser demo (`demo.html`) + XSS fix | `6ed26a3`, `e0b031d` |
| 5 | Meta-App Framework Extension (PluginManager + GUI dock + `q3n run`) | `a65699b` |
| 6 | Fortune Plugin (move FortuneOverlay → `app/plugins/fortune/`) | `aeee1cf` |

| 7 | Citation Formatter (`format_citation()` + tests) | `10eb801` |
| 8 | Citation Plugin Panel + `q3n cite` CLI alias | `a81c100` |

## Sprint Complete ✓

## Post-Sprint Changes

| Change | Commit |
|--------|--------|
| OSM/GIS URI schemes + icon fixes + website logo | `ec036cf` |
| Web migration + version bump 1.0.0 → 1.1.0 | `(pending)` |

### OSM/GIS URI Schemes
- `osm://node|way|relation|changeset/<id>` → `browse_url`, `api_url` in meta
- `geo:<lat>,<lon>[?z=<zoom>]` → `lat`, `lon`, `zoom`, `map_url` in meta
- `overpass://<query>` → `query`, `api_url` in meta
- All three added to `URI_PARSERS` and `SCHEME_REGISTRY` (category: `map`)
- `parse_scheme` extended to handle `scheme:path` (no `//`) for `geo:` and future colon-only schemes
- 13 new tests in `tests/test_osm.py`

### App Icon
- `gui/main_window.py` — `setWindowIcon` from `scripts/AppDir/q3n.png`
- `app/src/main.py` — `app.setWindowIcon` on startup
- `debian/rules` — installs icon to `/usr/share/pixmaps/q3n.png` so `.desktop` `Icon=q3n` resolves

### Website
- `docs/website/index.html` + `demo.html` — 72px/56px logo `<img>` in page header (same `favicon.png`)

### Web Migration + Version Bump

**Version:** `1.0.0` → `1.1.0` in `core/__init__.py` and `debian/changelog`

**`docs/website/` merged into `web/` and deleted.** Content migrated:
- `web/public/demo.html` — interactive live demo (back link updated from `index.html` → `/`; osm/geo scheme badges added)
- `web/public/q3n-parser.js` — JS parser for browser use
- `web/src/App.tsx` — expanded with: hero logo + "Try it live →" link; Overview section with 3 feature cards; Examples section with 4 format examples; Tools section (CLI, GUI, JS parser, VS Code); Getting Started section; updated scheme list (`osm · geo · overpass` added); footer license corrected to AGPL-3.0 with Anti-Fascist Exception
- `web/src/App.css` — added: `.hero__logo`, `.hero__link--accent`, `.section-desc`, `.features`/`.feature`, `.examples`/`.example__label`, section spacing
- `web/index.html` — PNG favicon added (SVG kept as fallback)

**Test result:** 160/160 passed (no regressions)

## Additional Pending Requests

### OSM/GIS URI Schemes
- `osm://node|way|relation|changeset/<id>` → `browse_url`, `api_url` in `as_dict()`
- `geo:<lat>,<lon>[?z=<zoom>]` → `map_url` in `as_dict()`
- `overpass://<query>` (stretch)
- GUI wizard: new source type pages; exports: clickable links; tests for all

### App Icon Not Displaying
Icon missing from: website favicon, .deb app menu, GUI titlebar.
Check: `q3n.desktop` icon field, `/usr/share/pixmaps/`, `debian/rules` install step.

## Resume
Base commit for next work: `a81c100`

## Task 8 Detail

**Files changed:**
- `app/plugins/cite/__init__.py` — `PLUGIN_META` + `register(manager)` (registers panel + standalone) + `_run_standalone` (argparse mini-parser for `--style`, `--entry`, `--all`)
- `app/plugins/cite/panel.py` — `CitePanelWidget`: vertical splitter with entry list (top) and citation text box (bottom); style combo; Copy to clipboard button; `set_entries` populates list and auto-selects row 0
- `tools/q3n` — `cmd_cite` function + `q3n cite [file] [--style] [--entry N] [--all]` subcommand

**Smoke test:** `q3n cite examples/sample.q3n --style mla --all` prints 7 MLA citations; `--style bibtex --entry 2` prints BibTeX `@book` for the ISBN entry.

**Test result:** 147/147 passed (no regressions)

## Task 7 Detail

**Files changed:**
- `app/plugins/cite/__init__.py` — created (empty, placeholder for Task 8)
- `app/plugins/cite/formatter.py` — `format_citation(entry, style)` engine; MLA 9, APA 7, Chicago 17, BibTeX; scheme-dispatched helpers per style; graceful degradation for missing author (`[n.a.]`) and year (`n.d.`/`[n.d.]`)
- `tests/test_cite.py` — 20 tests across all four styles and graceful-degradation cases; test assertion fixed (formatter replaces `_` with spaces in titles, so assertion checks for `'The Book'` not `'The_Book'`)

**Test result:** 147/147 passed (no regressions)
SDD ledger: `.superpowers/sdd/progress.md`
Plan: `docs/superpowers/plans/2026-06-27-feature-sprint.md`

## Task 6 Detail

**Files changed:**
- `app/plugins/__init__.py` — created (empty package marker)
- `app/plugins/fortune/__init__.py` — `PLUGIN_META` dict + `register(manager)` (registers panel + standalone) + `_run_standalone`
- `app/plugins/fortune/widget.py` — `FortuneOverlay` moved here from `app/src/widgets/fortune_widget.py`; fixed the `setCentralWidget` hack (was calling a QMainWindow method on QWidget — replaced with a plain outer `QVBoxLayout`); cleaned up unused imports
- `app/plugins/fortune/panel.py` — `FortunePanelWidget`: compact sidebar card with Next/Pop-out buttons; `set_entries` picks a random entry and displays quote + attribution
- `app/src/widgets/fortune_widget.py` — replaced with one-line re-export (`from app.plugins.fortune.widget import FortuneOverlay`) so existing callers don't break
- `app/src/main.py` — `_launch_fortune` updated to import directly from `app.plugins.fortune.widget`

**Test result:** 127/127 passed (no regressions)

## Task 5 Detail

**Files changed:**
- `app/src/core/plugin_manager.py` — added `_panels`, `_standalones` dicts to `__init__`; added `register_panel(name, widget_class)`, `register_standalone(name, func)`, `list_plugins() -> list[tuple]`, `run_standalone(name, entries, args)` methods; added `panels` property
- `gui/main_window.py` — added `QDockWidget`, `QTabWidget` imports; added `_plugin_panels`, `_plugin_dock` instance vars; added `load_plugins(manager)` (creates right-side dock with one tab per panel) and `_notify_plugins(entries)` (pushes entry list to all panels); wired `_notify_plugins` into `_load_entries` and `_on_entry_changed`
- `tools/q3n` — added `cmd_run` function and `q3n run <plugin> [file] [args...]` subcommand
- `tests/test_plugin_manager.py` — 6 new tests (register panel, register standalone, run standalone, KeyError on missing, list_plugins empty, list_plugins with module); all pass

**Test result:** 105/105 passed (no regressions)
