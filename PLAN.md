# Q3N Iteration Plan

A living document for improving this project without regressions. Each iteration follows the same discipline: tests pass before and after, docs stay in sync, every push goes through Woodpecker CI.

---

## The Rule: No Regressions, Ever

Before touching code:
1. `python3 -m pytest tests/ -v` — confirm baseline is green
2. Make changes
3. `python3 -m pytest tests/ -v` — confirm still green
4. Update docs if behaviour changed (README, ARCHITECTURE, CLAUDE.md, spec)
5. Commit, push — CI confirms on Python 3.9–3.12

If CI fails, fix it before starting the next iteration. Never pile work on a broken baseline.

---

## Iteration 1 — Test Coverage for New Schemes ✓ DONE

**Goal:** Write tests for `pubmed://`, `orcid://`, `spotify://` URI parsers (added in the consolidation commit but not yet covered by tests).

**Files:** `tests/test_q3n.py`

Tasks:
- [x] `test_parse_pubmed_uri` — `URI_PARSERS['pubmed']('pubmed://12345678')` → `{'type': 'academic', 'pmid': '12345678'}`
- [x] `test_parse_orcid_uri` — `URI_PARSERS['orcid']('orcid://0000-0002-1825-0097')` → `{'orcid': '0000-0002-1825-0097'}`
- [x] `test_parse_spotify_uri` — `URI_PARSERS['spotify']('spotify://track:4cOdK2wGLET')` → `{'kind': 'track', 'id': '4cOdK2wGLET'}`
- [x] `test_resolve_uri_pubmed` — attribution returns `"— Academic paper (pubmed)"`
- [x] `test_resolve_uri_orcid` — attribution returns `"— ORCID 0000-..."`
- [x] `test_resolve_uri_spotify` — attribution returns `"— Spotify track"`
- [x] Add entries for new schemes to `famous-quotes.q3n` to exercise them end-to-end

---

## Iteration 2 — JS Parser Parity ✓ DONE

**Goal:** Bring `src/js/q3n-parser.js` up to parity with `core/q3n.py`.

Tasks:
- [x] Add `parsePubmedUri`, `parseOrcidUri`, `parseSpotifyUri` to JS parser
- [x] Register them in `URI_PARSERS` and `SCHEME_CATEGORIES`
- [x] Add inline-`\\\` handling to JS `parse()`
- [x] Extend `test-q3n-parser.js` with new scheme tests (31 total, all passing)
- [x] Confirm `node src/js/test-q3n-parser.js` exits 0

---

## Iteration 3 — GUI: Filter Persistence & UX ✓ DONE

**Goal:** Polish the search/filter experience.

Tasks:
- [x] Replace fragile identity lookup in `_on_entry_changed` with `list.index()` (uses object identity since Q3NEntry has no __eq__)
- [x] Call `self._tag_filter.set_tags(self._all_entries)` after `_on_entry_changed`
- [x] Add `Ctrl+F` shortcut → `self._search_input.setFocus()`
- [x] Add `pubmed`, `orcid`, `spotify` scheme icons to `EntryDetailView` SCHEME_ICONS
- [x] Add metadata display for `pmid`, `orcid`, spotify `kind`/`id` fields

---

## Iteration 4 — Fortune Command Polish ✓ DONE

**Goal:** Make `q3n fortune` a first-class feature.

Tasks:
- [x] Add `fortune` export format to the GUI Export menu
- [x] Add `--filter-tag TAG` flag to `fortune` CLI subcommand
- [x] Add `--filter-scheme SCHEME` flag
- [x] Write 22 tests for `core/fortune.py` (format_fortune, box_text, display_fortune, export_fortune, pick_art)
- [x] Update `pick_art` to cover pubmed, orcid, spotify schemes

---

## Iteration 5 — Debian Package Cleanup ✓ DONE

**Goal:** The `debian/q3n/` tree (built output) should not be committed.

Tasks:
- [x] Add `debian/q3n/` and `debian/.debhelper/` to `.gitignore`
- [x] Remove already-committed build artifacts from git tracking (`git rm -r --cached`)
- Note: `dpkg-buildpackage` verification skipped (not available in current environment — CI handles this)

---

## Iteration 6 — Cloudflare Worker Download Site ✓ DONE

**Goal:** Ship a Vite + React Cloudflare Worker (`web/`) that serves a download page for Q3N packages (.deb, .tar.gz, .AppImage, future Flatpak). Assets are linked from GitHub Releases.

Tasks:
- [x] Scaffold `web/` from the vite-react-template pattern (Vite + React + `@cloudflare/vite-plugin`)
- [x] `wrangler.toml` with `name = "q3n-site"` and `compatibility_date`
- [x] React download page: .deb, .tar.gz, .AppImage; full feature sections; interactive browser demo
- [x] Deployed to https://q3n.distorted.work (CF Workers, custom domain)

Note: CI auto-deploy via wrangler is not yet wired; deployments are currently manual. Woodpecker CI does not deploy — pr-dashboard/approval not wired.

---

## Iteration 7 — Audit Remediation (All 23 Issues)

**Goal:** Fix every issue identified in the June 2026 project-wide audit. Each sub-iteration is ordered by impact (critical first). Tests must pass before and after each block.

### Block A — Critical bugs (5 issues)

- [x] **A1 — CLI export broken for html/index/fortune** (`tools/q3n:643-654`)
  Fix: Replace inline format dispatch with call to `core.q3n.export_file(entries, path, fmt)` — eliminates duplicate logic and all three broken formats at once. Update argparse choices if needed.

- [x] **A2 — GUI dirty-flag bug on entry switch** (`gui/entry_view.py:143-149`)
  Fix: Wrap `show_entry()` field population with `blockSignals(True/False)` so `setText`/`setPlainText` doesn't trigger `_mark_dirty`. Set `_dirty = False` after all fields are populated.

- [x] **A3 — app/ package excluded from pip install** (`setup.py:12`)
  Fix: Change `find_packages(include=['core', 'core.*', 'gui', 'gui.*'])` to `find_packages()` (includes `app`, `app.plugins.*`, `app.src.*`). Ensure `MANIFEST.in` or `package_data` covers non-.py files in `app/`.

- [x] **A4 — q3n.png not tracked in git, breaks debian/rules** (`scripts/AppDir/q3n.png`, `.gitignore:52`)
  Fix: Remove `scripts/AppDir/q3n.png` from `.gitignore` and `git add` it. Or move icon to a tracked location and update `debian/rules` path.

- [x] **A5 — JS parser missing osm/geo/overpass schemes** (`src/js/q3n-parser.js`)
  Fix: Implement `parseOsmUri`, `parseGeoUri`, `parseOverpassUri` in JS. Register in `URI_PARSERS` and `SCHEME_CATEGORIES`. Add tests to `test-q3n-parser.js`. Copy same fix to `web/public/q3n-parser.js`.

### Block B — High-impact bugs (6 issues)

- [x] **B1 — ConfigParser % interpolation crash** (`core/config.py:46`)
  Fix: `configparser.ConfigParser(interpolation=None)` — prevents crash when config values contain `%`.

- [x] **B2 — parse_yt_uri dead code + list-vs-string bug** (`core/q3n.py:138-139`)
  Fix: Remove unreachable `if rest.startswith('watch?v=')` branch. The `?` branch handles this case correctly via `parse_qs`.

- [x] **B3 — Bare `except Exception: pass` in 3 locations** (`core/q3n.py:383,630,643`)
  Fix: Narrow to specific exception types (`OSError`, `ValueError`, `json.JSONDecodeError`, etc.). Never catch `KeyboardInterrupt` or `MemoryError`.

- [x] **B4 — Delete dead `entry_dialog.py`** (`gui/entry_dialog.py`)
  Fix: Remove file. Update `ARCHITECTURE.md` if it references `EntryDialog`.

- [x] **B5 — Silent failure in `open_path`** (`gui/main_window.py:530-531`)
  Fix: Replace bare `except Exception: pass` with error dialog via `QMessageBox.critical` (same pattern as `_open_file` at line 483-484).

- [x] **B6 — Plugin dock can't be restored after close** (`gui/main_window.py:697-706`)
  Fix: Add View menu action to toggle plugin dock visibility. Use `QMenu.addAction(dock.toggleViewAction())`.

### Block C — Documentation fixes (5 issues)

- [x] **C1 — Man page stale** (`docs/man/q3n.1`)
  Fix: Bump header version to 1.1.4. List all 7 export formats in `export` section. Add `-c`/`--count` and `--art` to `fortune` section. Add `--version` to SYNOPSIS.

- [x] **C2 — ARCHITECTURE.md inaccuracies** (`ARCHITECTURE.md`)
  Fix: Add `config` to subcommand list. Fix JS API method names (`toJSON` → `exportJson`, etc.). Remove false claim that JS supports osm/geo/overpass (or mark as incomplete).

- [x] **C3 — Specification.md stale** (`docs/format/specification.md`)
  Fix: Bump version to v1.1.4. Move OSM/GIS scheme addition from v1.1.3 to v1.1.0 in version history. Add EBNF rule for inline `\\\` closing.

- [x] **C4 — CLI lint scope mismatch** (`CLAUDE.md:19-20` vs `.github/workflows/ci.yml:32-33`)
  Fix: Either add `app/plugins/` and `gui/` to CI lint command, or update CLAUDE.md to match actual CI scope.

- [x] **C5 — BUILDING.md wrong AppImage method** (`BUILDING.md:47-61`)
  Fix: Replace `pyside6-deploy`/`pyproject-appimage` instructions with the actual PyInstaller-based build (`scripts/q3n.spec` + `scripts/build-appimage.sh`).

### Block D — Packaging gaps (6 issues)

- [x] **D1 — q3n.appdata.xml version outdated** (`q3n.appdata.xml:30`)
  Fix: Add `<release version="1.1.4" date="2026-06-30">` entry.

- [x] **D2 — debian/rules hardcodes Python 3.13** (`debian/rules:9`)
  Fix: Use `$(shell ls build/scripts-* 2>/dev/null)` or `find` instead of hardcoded `build/scripts-3.13`.

- [x] **D3 — Git tag v1.1.0 missing** (debian/changelog vs tags)
  Fix: Create annotated tag `v1.1.0` at the appropriate commit, or remove the changelog entry.

- [x] **D4 — CI never installs PySide6** (`.github/workflows/ci.yml:26-28`)
  Fix: Add `pip install PySide6` or create `requirements.txt` with core deps. Import tests for GUI won't work without it.

- [x] **D5 — q3n config --install path resolution** (`tools/q3n:1073-1076`)
  Fix: When `tools/q3n` is installed to `/usr/bin/`, `repo_root` resolves wrong. Add fallback to search `sys.path` or `__file__`-relative paths for `examples/`.

- [x] **D6 — JS parser files are duplicated** (`src/js/q3n-parser.js` and `web/public/q3n-parser.js`)
  Fix: Either symlink `web/public/q3n-parser.js` → `../../src/js/q3n-parser.js`, or use a build step to copy, or add a CI check that they're identical.

## Ongoing: Documentation Sync Discipline

After every code change that touches public API or CLI behaviour:

| Changed | Update |
|---------|--------|
| New/removed CLI subcommand | `README.md` command table, `ARCHITECTURE.md`, `CLAUDE.md` |
| New URI scheme | `README.md` schemes list, `ARCHITECTURE.md`, `docs/format/specification.md`, `core/q3n.py` SCHEME_REGISTRY + URI_PARSERS, CLI SCHEME_COLORS + SCHEME_ICONS, GUI SCHEME_DISPLAY_ICONS |
| New export format | `README.md`, `ARCHITECTURE.md`, `docs/format/specification.md` |
| `Q3NEntry` API change | `ARCHITECTURE.md`, `CLAUDE.md` |
| New test file | `CLAUDE.md` testing conventions section |

The CI `docs` job only checks that the files exist — a future iteration should add a linting step that catches stale scheme lists.

---

## Iteration 8 — New Features

### Block E — URI Schemes (2 additions)

**E1 — `wikipedia://` scheme** (~30 min)

Syntax: `wikipedia://Article_Title` or `wikipedia://en/Article_Title`

`parse_wikipedia_uri()` strips scheme, splits optional language prefix, returns `{'type': 'web', 'article': title, 'lang': lang, 'browse_url': ...}`. Registered in `SCHEME_REGISTRY` as `'web'` and `URI_PARSERS`. Validated for non-empty title. Standard 11-file touch pattern (core, CLI colors/icons/wizard/help, GUI wizard/types/icons, fortune pick_art, tests, JS).

**E2 — `github://` scheme** (~45 min)

Syntax: `github://user/repo`, `github://user/repo/issues/123`, `github://user/repo/pull/45`, `github://user/repo/commit/abc123`, `github://user/repo/discussions/7`

`parse_github_uri()` extracts owner/repo, optional kind/id, builds `browse_url` + `label`. Validates non-empty owner/repo. Same 11-file touch pattern.

### Block F — Export Plugins (2 additions)

**F1 — Anki export plugin** (`app/plugins/anki/` ~2 hrs)

CSV export compatible with Anki import (fields: Quote, Source, Tag, URI). Optional `.apkg` via `genanki`. Registered as `anki` format in `export_file()`. Plugin: `__init__.py` + `panel.py` + `export.py`. Optional dep in `setup.py extras_require`.

**F2 — Obsidian export plugin** (`app/plugins/obsidian/` ~1.5 hrs)

Individual `.md` files per entry with YAML frontmatter (source, scheme, tag, created) + blockquote body. Tag→folder mapping option. Registered as `obsidian` format in `export_file()`.

### Block G — Tag management CLI (~2 hrs)

Subcommands: `q3n tag list [dir]`, `q3n tag show <tag> [dir]`, `q3n tag rename <old> <new> [dir]`, `q3n tag delete <tag> [dir]`, `q3n tag merge <from> <into> [dir]`. Reuses stats counting, in-place file rewrite with confirmation prompts.

### Block H — LLM auto-tagging plugin (`app/plugins/autotag/` ~2 hrs)

Sends quote text + URI to OpenAI-compatible endpoint, parses response into tag suggestions. Accept/reject per tag in GUI panel. API key/config in `q3n.conf`. CLI: `--dry-run` flag.

### Block I — Capture daemon + global hotkey + browser extension (~4 hrs)

Daemon (`bin/q3n-capture-daemon`): lightweight HTTP server on localhost:9876, receives `{url, quote, tag, title}` via POST, appends to Q3N file.

Global hotkey script (`bin/q3n-capture`): registers `Ctrl+Shift+Q`, reads clipboard, opens popup, saves via daemon.

Browser extension (Chrome/Firefox): right-click "Save to Q3N" sends `{url, selectionText, title}` to daemon. No popup form (MVP). Tags as `web/clippings`.

### Implementation order

| # | Feature | Effort |
|---|---------|--------|
| 1 | `wikipedia://` scheme | 30 min |
| 2 | `github://` scheme | 45 min |
| 3 | Tag management CLI | 2 hrs |
| 4 | Anki export plugin | 2 hrs |
| 5 | Obsidian export plugin | 1.5 hrs |
| 6 | LLM auto-tagging plugin | 2 hrs |
| 7 | Capture daemon + hotkey + browser extension | 4 hrs |
