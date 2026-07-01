"""Tests for core/q3n.py — parse, serialize, export, detect, and URI resolution."""

from pathlib import Path
import json
import tempfile
import sys

_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from core.q3n import (
    Q3NEntry,
    parse,
    parse_file,
    serialize,
    export_json,
    export_markdown,
    export_html,
    export_plaintext,
    generate_index,
    detect,
    list_entries,
    resolve_uri,
    parse_scheme,
    URI_PARSERS,
    SCHEME_REGISTRY,
    detect_content_type,
)


SAMPLE = r"""#!q3n-format

/// https://example.com/article
The quick brown fox jumps over the lazy dog.
This is a second line of the quote.
\\\

/// isbn://978-0-13-468599-1;The_Pragmatic_Programmer;Andy_Hunt;1999 /// book:
Software is a creative process.
\\\

/// q3n://author:john;john@example.com;'John Doe' /// person:
A person reference entry.
\\\
"""


# ── Basic Parsing ──────────────────────────────────────────────────────


def test_parse_returns_correct_number_of_entries():
    entries = parse(SAMPLE)
    assert len(entries) == 3


def test_parse_web_entry():
    entries = parse(SAMPLE)
    e = entries[0]
    assert e.scheme == 'https'
    assert e.uri == 'https://example.com/article'
    assert 'quick brown fox' in e.quote
    assert e.tag is None


def test_parse_isbn_entry():
    entries = parse(SAMPLE)
    e = entries[1]
    assert e.scheme == 'isbn'
    assert 'isbn://' in e.uri
    assert e.tag == 'book'


def test_parse_person_entry():
    entries = parse(SAMPLE)
    e = entries[2]
    assert e.scheme == 'q3n'
    assert e.tag == 'person'


def test_parse_empty_returns_empty():
    assert parse('') == []


def test_parse_no_match_returns_empty():
    assert parse('Just some text without Q3N markers.') == []


# ── Scheme Parsing ─────────────────────────────────────────────────────


def test_parse_scheme_https():
    s, p = parse_scheme('https://example.com/page')
    assert s == 'https'
    assert 'example.com' in p


def test_parse_scheme_no_scheme():
    s, p = parse_scheme('plaintext')
    assert s == ''
    assert p == 'plaintext'


def test_parse_scheme_isbn():
    s, p = parse_scheme('isbn://978-0-13-468599-1')
    assert s == 'isbn'


def test_parse_scheme_q3n():
    s, p = parse_scheme('q3n://handle:id')
    assert s == 'q3n'


# ── URI Parsers (scheme-specific) ──────────────────────────────────────


def test_parse_web_uri_with_fragment():
    meta = URI_PARSERS['https']('https://example.com/page#section-3')
    assert meta['domain'] == 'example.com'
    assert meta['fragment'] == 'section-3'


def test_parse_web_uri_with_query_params():
    meta = URI_PARSERS['https']('https://example.com/search?q=test&lang=en')
    assert meta['domain'] == 'example.com'
    assert meta['query_params'] == {'q': ['test'], 'lang': ['en']}


def test_parse_q3n_uri():
    meta = URI_PARSERS['q3n']("q3n://john:123;email@test.com;'John Smith'")
    assert meta['type'] == 'person'
    assert meta['handle'] == 'john'
    assert meta['id'] == '123'
    assert meta['email'] == 'email@test.com'
    assert meta['name'] == 'John Smith'


def test_parse_q3n_uri_minimal():
    meta = URI_PARSERS['q3n']('q3n://user:abc')
    assert meta['handle'] == 'user'
    assert meta['id'] == 'abc'


def test_parse_isbn_uri():
    meta = URI_PARSERS['isbn']("isbn://978-0-13-468599-1;Title;Author;2024")
    assert meta['isbn'] == '978-0-13-468599-1'
    assert meta['title'] == 'Title'
    assert meta['author'] == 'Author'
    assert meta['year'] == 2024


def test_parse_isbn_uri_minimal():
    meta = URI_PARSERS['isbn']('isbn://978-0-13-468599-1')
    assert meta['isbn'] == '978-0-13-468599-1'
    assert 'title' not in meta


def test_parse_doi_uri():
    meta = URI_PARSERS['doi']('doi://10.1000/xyz123')
    assert meta['doi'] == '10.1000/xyz123'


def test_parse_arxiv_uri():
    meta = URI_PARSERS['arxiv']('arxiv://2301.00001')
    assert meta['arxiv_id'] == '2301.00001'


def test_parse_yt_uri():
    meta = URI_PARSERS['yt']('yt://dQw4w9WgXcQ')
    assert meta['video_id'] == 'dQw4w9WgXcQ'
    assert meta['platform'] == 'youtube'


def test_parse_yt_uri_with_timestamp():
    meta = URI_PARSERS['yt']('yt://dQw4w9WgXcQ?t=42')
    assert meta['video_id'] == 'dQw4w9WgXcQ'
    assert meta['timestamp'] == 42


def test_parse_file_uri():
    meta = URI_PARSERS['file']('file:///home/user/doc.txt#line=42')
    assert meta['path'] == '/home/user/doc.txt'
    assert meta['line'] == 42


def test_parse_pubmed_uri():
    meta = URI_PARSERS['pubmed']('pubmed://12345678')
    assert meta['type'] == 'academic'
    assert meta['pmid'] == '12345678'


def test_parse_orcid_uri():
    meta = URI_PARSERS['orcid']('orcid://0000-0002-1825-0097')
    assert meta['type'] == 'person'
    assert meta['orcid'] == '0000-0002-1825-0097'


def test_parse_spotify_uri_track():
    meta = URI_PARSERS['spotify']('spotify://track:4cOdK2wGLETKBW3PvgPWqT')
    assert meta['type'] == 'media'
    assert meta['platform'] == 'spotify'
    assert meta['kind'] == 'track'
    assert meta['id'] == '4cOdK2wGLETKBW3PvgPWqT'


def test_parse_spotify_uri_album():
    meta = URI_PARSERS['spotify']('spotify://album:1DFixLWuPkv3KT3TnV35m3')
    assert meta['kind'] == 'album'
    assert meta['id'] == '1DFixLWuPkv3KT3TnV35m3'


def test_parse_spotify_uri_bare():
    meta = URI_PARSERS['spotify']('spotify://4cOdK2wGLETKBW3PvgPWqT')
    assert meta['id'] == '4cOdK2wGLETKBW3PvgPWqT'


def test_parse_wikipedia_uri():
    meta = URI_PARSERS['wikipedia']('wikipedia://Quantum_mechanics')
    assert meta['type'] == 'web'
    assert meta['article'] == 'Quantum_mechanics'
    assert meta['lang'] == 'en'
    assert 'en.wikipedia.org' in meta['browse_url']


def test_parse_wikipedia_uri_with_lang():
    meta = URI_PARSERS['wikipedia']('wikipedia://fr/Paris')
    assert meta['article'] == 'Paris'
    assert meta['lang'] == 'fr'
    assert 'fr.wikipedia.org' in meta['browse_url']


def test_parse_github_uri():
    meta = URI_PARSERS['github']('github://torvalds/linux')
    assert meta['type'] == 'web'
    assert meta['platform'] == 'github'
    assert meta['owner'] == 'torvalds'
    assert meta['repo'] == 'linux'
    assert meta['kind'] is None
    assert 'github.com/torvalds/linux' in meta['browse_url']


def test_parse_github_uri_with_kind():
    meta = URI_PARSERS['github']('github://user/repo/issues/123')
    assert meta['owner'] == 'user'
    assert meta['repo'] == 'repo'
    assert meta['kind'] == 'issues'
    assert meta['id'] == '123'
    assert 'issues/123' in meta['browse_url']


def test_resolve_uri_github():
    uri_data = {'scheme': 'github', 'uri': 'github://torvalds/linux',
                'meta': {'label': 'torvalds/linux', 'owner': 'torvalds', 'repo': 'linux'}}
    result = resolve_uri(uri_data)
    assert 'GitHub' in result
    assert 'torvalds/linux' in result


# ── Resolve URI (attribution) ──────────────────────────────────────────


def test_resolve_uri_web():
    uri_data = {'scheme': 'https', 'uri': 'https://example.com', 'meta': {'domain': 'example.com'}}
    result = resolve_uri(uri_data)
    assert 'example.com' in result


def test_resolve_uri_q3n():
    uri_data = {'scheme': 'q3n', 'uri': 'q3n://j:1', 'meta': {'name': 'Jane'}}
    assert 'Jane' in resolve_uri(uri_data)


def test_resolve_uri_isbn():
    uri_data = {'scheme': 'isbn', 'uri': 'isbn://x', 'meta': {'author': 'Test', 'title': 'Book'}}
    result = resolve_uri(uri_data)
    assert 'Test' in result
    assert 'Book' in result


def test_resolve_uri_pubmed():
    uri_data = {'scheme': 'pubmed', 'uri': 'pubmed://12345678', 'meta': {'pmid': '12345678'}}
    result = resolve_uri(uri_data)
    assert 'pubmed' in result


def test_resolve_uri_orcid():
    uri_data = {'scheme': 'orcid', 'uri': 'orcid://0000-0002-1825-0097',
                'meta': {'orcid': '0000-0002-1825-0097'}}
    result = resolve_uri(uri_data)
    assert '0000-0002-1825-0097' in result


def test_resolve_uri_spotify():
    uri_data = {'scheme': 'spotify', 'uri': 'spotify://track:abc',
                'meta': {'kind': 'track', 'id': 'abc', 'platform': 'spotify'}}
    result = resolve_uri(uri_data)
    assert 'Spotify' in result
    assert 'track' in result


def test_resolve_uri_wikipedia():
    uri_data = {'scheme': 'wikipedia', 'uri': 'wikipedia://Quantum_mechanics',
                'meta': {'article': 'Quantum_mechanics', 'lang': 'en'}}
    result = resolve_uri(uri_data)
    assert 'Wikipedia' in result
    assert 'Quantum mechanics' in result


# ── Scheme registry ────────────────────────────────────────────────────


def test_scheme_registry_new_schemes():
    assert SCHEME_REGISTRY['pubmed'] == 'academic'
    assert SCHEME_REGISTRY['orcid'] == 'person'
    assert SCHEME_REGISTRY['spotify'] == 'media'
    assert SCHEME_REGISTRY['wikipedia'] == 'web'
    assert SCHEME_REGISTRY['github'] == 'web'


def test_entry_category_pubmed():
    e = Q3NEntry('pubmed://12345678', 'pubmed', '12345678', 'Results were significant.')
    d = e.as_dict()
    assert d['category'] == 'academic'
    assert d['meta']['pmid'] == '12345678'


def test_entry_category_orcid():
    e = Q3NEntry('orcid://0000-0002-1825-0097', 'orcid', '0000-0002-1825-0097', 'Cited work.')
    d = e.as_dict()
    assert d['category'] == 'person'
    assert d['meta']['orcid'] == '0000-0002-1825-0097'


def test_entry_category_spotify():
    e = Q3NEntry('spotify://track:4cOdK2w', 'spotify', 'track:4cOdK2w', 'Lyric excerpt.')
    d = e.as_dict()
    assert d['category'] == 'media'
    assert d['meta']['kind'] == 'track'


# ── Q3NEntry ───────────────────────────────────────────────────────────


def test_entry_as_dict_includes_derived_data():
    e = Q3NEntry(
        uri='https://example.com',
        scheme='https',
        path='example.com',
        quote='Test quote',
        tag='web',
    )
    d = e.as_dict()
    assert d['uri'] == 'https://example.com'
    assert d['scheme'] == 'https'
    assert d['quote'] == 'Test quote'
    assert d['tag'] == 'web'
    assert d['category'] == 'web'
    assert 'meta' in d


def test_entry_attribution():
    e = Q3NEntry('https://example.com', 'https', 'example.com', 'Hello')
    assert 'example.com' in e.attribution()


def test_entry_repr():
    e = Q3NEntry('https://x.com', 'https', 'x.com', 'Short')
    r = repr(e)
    assert 'Q3NEntry' in r
    assert 'https' in r


def test_entry_no_tag():
    e = Q3NEntry('https://x.com', 'https', 'x.com', 'No tag')
    assert e.tag is None


# ── Serialization ──────────────────────────────────────────────────────


def test_serialize_roundtrip():
    entries = parse(SAMPLE)
    output = serialize(entries)
    re_parsed = parse(output)
    assert len(re_parsed) == len(entries)
    for orig, rep in zip(entries, re_parsed):
        assert orig.uri == rep.uri
        assert orig.quote == rep.quote
        assert orig.tag == rep.tag


def test_serialize_no_header():
    entries = parse(SAMPLE)
    output = serialize(entries, header=False)
    assert '#!q3n-format' not in output.split('\n')[0]


# ── Detection ──────────────────────────────────────────────────────────


def test_detect_by_extension(tmp_path):
    f = tmp_path / 'test.q3n'
    f.write_text('')
    assert detect(f)


def test_detect_by_extension_q3nt(tmp_path):
    f = tmp_path / 'test.q3nt'
    f.write_text('')
    assert detect(f)


def test_detect_by_content_header(tmp_path):
    f = tmp_path / 'test.txt'
    f.write_text('#!q3n-format\n')
    assert detect(f)


def test_detect_by_content_pattern(tmp_path):
    f = tmp_path / 'test.txt'
    f.write_text('/// https://example.com\nquote\n\\\\\\\n')
    assert detect(f)


def test_detect_non_q3n(tmp_path):
    f = tmp_path / 'test.txt'
    f.write_text('Just some text.')
    assert not detect(f)


def test_detect_nonexistent(tmp_path):
    assert not detect(tmp_path / 'nonexistent.q3n')


# ── File roundtrip ─────────────────────────────────────────────────────


def test_parse_file_roundtrip(tmp_path):
    f = tmp_path / 'test.q3n'
    f.write_text(SAMPLE)
    entries = parse_file(f)
    assert len(entries) == 3
    output = serialize(entries)
    f2 = tmp_path / 'roundtrip.q3n'
    f2.write_text(output)
    re_read = parse_file(f2)
    assert len(re_read) == 3
    assert re_read[0].quote == entries[0].quote
    assert re_read[1].tag == entries[1].tag


# ── Export formats ─────────────────────────────────────────────────────


def test_export_json_parses():
    entries = parse(SAMPLE)
    data = json.loads(export_json(entries))
    assert len(data) == 3
    assert data[0]['scheme'] == 'https'


def test_export_markdown_includes_entry_count():
    entries = parse(SAMPLE)
    md = export_markdown(entries)
    assert 'Q3N Collection' in md
    assert 'Entry 1' in md
    assert 'Entry 2' in md
    assert 'Entry 3' in md


def test_export_markdown_blockquotes():
    entries = parse(SAMPLE)
    md = export_markdown(entries)
    assert '> The quick brown fox' in md


def test_export_html_structure():
    entries = parse(SAMPLE)
    html = export_html(entries)
    assert '<html>' in html
    assert 'blockquote' in html
    assert 'Q3N Collection' in html
    assert 'example.com' in html


def test_export_plaintext():
    entries = parse(SAMPLE)
    text = export_plaintext(entries)
    assert 'Source:' in text
    assert '---' in text


def test_generate_index():
    entries = parse(SAMPLE)
    idx = generate_index(entries)
    assert 'Q3N Index' in idx
    assert 'Total entries: 3' in idx
    assert 'By Tag' in idx


# ── Import ─────────────────────────────────────────────────────────────


def test_import_json(tmp_path):
    entries = parse(SAMPLE)
    json_path = tmp_path / 'data.json'
    json_path.write_text(export_json(entries))
    from core.q3n import import_json
    imported = import_json(json_path)
    assert len(imported) == 3
    assert imported[0].uri == entries[0].uri
    assert imported[0].quote == entries[0].quote


# ── List entries ───────────────────────────────────────────────────────


def test_list_entries(tmp_path):
    f = tmp_path / 'test.q3n'
    f.write_text(SAMPLE)
    results = list_entries(tmp_path)
    assert len(results) >= 1
    found = any(p.name == 'test.q3n' for p, _ in results)
    assert found


def test_list_entries_skips_non_q3n(tmp_path):
    f = tmp_path / 'test.txt'
    f.write_text('Not Q3N')
    results = list_entries(tmp_path)
    assert len(results) == 0


# ── Edge cases ─────────────────────────────────────────────────────────


def test_parse_malformed_no_closing():
    text = '/// https://example.com\nIncomplete entry\n'
    entries = parse(text)
    assert len(entries) == 0


def test_parse_multiple_entries_same_source():
    text = r"""/// https://example.com
First quote.
\\\

/// https://example.com
Second quote.
\\\
"""
    entries = parse(text)
    assert len(entries) == 2
    assert entries[0].uri == entries[1].uri


def test_parse_quote_with_blank_lines():
    text = r"""/// https://example.com
Line one.

Line three.
\\\
"""
    entries = parse(text)
    assert len(entries) == 1
    assert 'Line one' in entries[0].quote
    assert 'Line three' in entries[0].quote


def test_parse_tag_with_slash_hierarchy():
    text = r"""/// https://example.com /// note/idea:
Tag with hierarchy.
\\\
"""
    entries = parse(text)
    assert len(entries) == 1
    assert entries[0].tag == 'note/idea'


# ── Content type detection (extended syntax) ──────────────────────────


def test_detect_content_type_text():
    assert detect_content_type('Just a regular quote.') == 'text'


def test_detect_content_type_json():
    text = '{"key": "value", "nested": [1, 2, 3]}'
    assert detect_content_type(text) == 'json'


def test_detect_content_type_json_strict():
    text = '{"code": "// comment", "data": {"type": "example"}}'
    assert detect_content_type(text) == 'json'


def test_detect_content_type_code_def():
    assert detect_content_type('def hello():\n    return 42') == 'code'


def test_detect_content_type_code_class():
    assert detect_content_type('class Foo:\n    pass') == 'code'


def test_detect_content_type_code_import():
    assert detect_content_type('import sys\nimport os') == 'code'


def test_detect_content_type_code_fence():
    assert detect_content_type('```python\nprint("hello")\n```') == 'code'


def test_detect_content_type_empty():
    assert detect_content_type('') == 'text'


def test_detect_content_type_blank():
    assert detect_content_type('   \n  ') == 'text'


def test_detect_content_type_code_keyword_ratio():
    text = 'def foo():\n    pass\n# comment\nprint("done")'
    assert detect_content_type(text) == 'code'


# ── Extended syntax: JSON in quote body ───────────────────────────────


JSON_ENTRY = r"""/// https://api.example.com/data
{
  "code": "// Example",
  "structured": true,
  "data": {
    "type": "example",
    "nested": [1, 2, 3]
  }
}
\\\
"""

CODE_ENTRY = r"""/// q3n://langdev:python;python@python.org;'Python'?lang=python
def example_function():
    return "Q3N is versatile!"
\\\
"""


def test_parse_json_entry():
    entries = parse(JSON_ENTRY)
    assert len(entries) == 1
    e = entries[0]
    assert 'structured' in e.quote
    assert e.as_dict()['content_type'] == 'json'


def test_parse_code_entry():
    entries = parse(CODE_ENTRY)
    assert len(entries) == 1
    e = entries[0]
    assert 'def example_function' in e.quote
    assert e.as_dict()['content_type'] == 'code'


def test_extended_syntax_roundtrip():
    combined = JSON_ENTRY + '\n' + CODE_ENTRY
    entries = parse(combined)
    assert len(entries) == 2
    assert entries[0].as_dict()['content_type'] == 'json'
    assert entries[1].as_dict()['content_type'] == 'code'
