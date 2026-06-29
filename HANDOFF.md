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
| 5 | Meta-App Framework Extension (PluginManager + GUI dock + `q3n run`) | pending push |

## Remaining Sprint Tasks

| # | Task |
|---|------|
| 6 | Fortune Plugin (move FortuneOverlay → `app/plugins/fortune/`) |
| 7 | Citation Formatter (`format_citation()` + tests) |
| 8 | Citation Plugin Panel + `q3n cite` CLI alias |

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
Base commit for Task 6: pending (Task 5 commit)
SDD ledger: `.superpowers/sdd/progress.md`
Plan: `docs/superpowers/plans/2026-06-27-feature-sprint.md`

## Task 5 Detail

**Files changed:**
- `app/src/core/plugin_manager.py` — added `_panels`, `_standalones` dicts to `__init__`; added `register_panel(name, widget_class)`, `register_standalone(name, func)`, `list_plugins() -> list[tuple]`, `run_standalone(name, entries, args)` methods; added `panels` property
- `gui/main_window.py` — added `QDockWidget`, `QTabWidget` imports; added `_plugin_panels`, `_plugin_dock` instance vars; added `load_plugins(manager)` (creates right-side dock with one tab per panel) and `_notify_plugins(entries)` (pushes entry list to all panels); wired `_notify_plugins` into `_load_entries` and `_on_entry_changed`
- `tools/q3n` — added `cmd_run` function and `q3n run <plugin> [file] [args...]` subcommand
- `tests/test_plugin_manager.py` — 6 new tests (register panel, register standalone, run standalone, KeyError on missing, list_plugins empty, list_plugins with module); all pass

**Test result:** 105/105 passed (no regressions)
