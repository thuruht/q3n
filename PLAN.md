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

## Iteration 2 — JS Parser Parity

**Goal:** Bring `src/js/q3n-parser.js` up to parity with `core/q3n.py`.

Known gaps:
- JS parser does not handle the inline `\\\` variant (closing marker at end of last quote line) that Python supports
- JS is missing `pubmed`, `orcid`, `spotify` URI parsers
- `src/js/test-q3n-parser.js` should be audited and extended to cover edge cases mirroring `tests/test_q3n.py`

Tasks:
- [ ] Add `parsePubmedUri`, `parseOrcidUri`, `parseSpotifyUri` to JS parser
- [ ] Register them in `URI_PARSERS` and `SCHEME_CATEGORIES`
- [ ] Add inline-`\\\` handling to JS `parse()`
- [ ] Extend `test-q3n-parser.js` with new scheme tests
- [ ] Confirm `node src/js/test-q3n-parser.js` exits 0

---

## Iteration 3 — GUI: Filter Persistence & UX

**Goal:** Polish the search/filter experience.

Known issues / improvements:
- After filtering, selecting an entry and editing it should update `_all_entries` reliably (current identity-based lookup is fragile — replace with index tracking)
- Tag filter dropdown should update when an entry's tag is edited
- Add keyboard shortcut `Ctrl+F` to focus the search box
- `EntryDetailView` should show the scheme icon next to the URI field

Tasks:
- [ ] Replace identity-based `_on_entry_changed` lookup with a cleaner approach (store `(all_entries_index, visible_index)` mapping when filter is applied)
- [ ] Call `self._tag_filter.set_tags(self._all_entries)` after `_on_entry_changed`
- [ ] Add `Ctrl+F` shortcut → `self._search_input.setFocus()`
- [ ] Add scheme icon label next to URI field in `EntryDetailView`

---

## Iteration 4 — Fortune Command Polish

**Goal:** Make `q3n fortune` a first-class feature.

Tasks:
- [ ] Add `fortune` export format to the GUI Export menu (currently only in CLI)
- [ ] Add `--filter-tag TAG` flag to `fortune` CLI subcommand
- [ ] Add `--filter-scheme SCHEME` flag (e.g. show only `isbn://` quotes)
- [ ] Write tests for `core/fortune.py` (`format_fortune`, `box_text`, `display_fortune`)

---

## Iteration 5 — Debian Package Cleanup

**Goal:** The `debian/q3n/` tree (built output) should not be committed.

Tasks:
- [ ] Add `debian/q3n/` to `.gitignore`
- [ ] Add `debian/.debhelper/` to `.gitignore`
- [ ] Remove the already-committed built files from git tracking (`git rm -r --cached debian/q3n/ debian/.debhelper/`)
- [ ] Verify `dpkg-buildpackage -us -uc -b` still produces a correct `.deb` from source

---

## Iteration 6 — Website

**Goal:** Publish `docs/website/index.html` via GitHub Pages.

Tasks:
- [ ] Add a GitHub Pages workflow (`.github/workflows/pages.yml`) that publishes `docs/website/` to the `gh-pages` branch on push to `main`
- [ ] Update internal links in `index.html` to point to the correct GitHub paths (currently some point to old repo structure)
- [ ] Add a `CNAME` file if a custom domain is wanted

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
