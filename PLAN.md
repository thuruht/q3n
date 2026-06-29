# Q3N Iteration Plan

A living document for improving this project without regressions. Each iteration follows the same discipline: tests pass before and after, docs stay in sync, every push goes through CI.

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

Note: CI auto-deploy via wrangler is not yet wired; deployments are currently manual.

---

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
