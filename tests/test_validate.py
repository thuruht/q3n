import pytest
from core.q3n import validate_uri, Q3NEntry, parse


def _entry(uri):
    entries = parse(f'/// {uri}\ntest\n\\\\\\')
    return entries[0]


# https / http
def test_https_valid():
    assert validate_uri('https://example.com/article') == []

def test_https_missing_host():
    errs = validate_uri('https://')
    assert len(errs) == 1
    assert 'host' in errs[0]

def test_http_valid():
    assert validate_uri('http://example.com') == []


# isbn
def test_isbn13_valid():
    assert validate_uri('isbn://978-0-14-303943-3') == []

def test_isbn13_bad_checksum():
    errs = validate_uri('isbn://978-0-14-303943-0')
    assert len(errs) == 1
    assert 'ISBN-13' in errs[0]

def test_isbn10_valid():
    assert validate_uri('isbn://0-306-40615-2') == []

def test_isbn10_bad_checksum():
    errs = validate_uri('isbn://0-306-40615-0')
    assert len(errs) == 1
    assert 'ISBN-10' in errs[0]

def test_isbn_wrong_length():
    errs = validate_uri('isbn://12345')
    assert len(errs) == 1
    assert 'length' in errs[0]


# doi
def test_doi_valid():
    assert validate_uri('doi://10.1038/s41586-019-1093-1') == []

def test_doi_invalid():
    errs = validate_uri('doi://not-a-doi')
    assert len(errs) == 1
    assert 'DOI' in errs[0]


# arxiv
def test_arxiv_new_format_valid():
    assert validate_uri('arxiv://2301.00001') == []

def test_arxiv_versioned_valid():
    assert validate_uri('arxiv://2301.00001v2') == []

def test_arxiv_legacy_valid():
    assert validate_uri('arxiv://cs.LG/0612056') == []

def test_arxiv_invalid():
    errs = validate_uri('arxiv://not-valid')
    assert len(errs) == 1
    assert 'arXiv' in errs[0]


# yt
def test_yt_valid():
    assert validate_uri('yt://dQw4w9WgXcQ') == []

def test_yt_invalid_video_id():
    errs = validate_uri('yt://short')
    assert len(errs) == 1
    assert '11' in errs[0]


# q3n
def test_q3n_valid():
    assert validate_uri("q3n://aristotle:384-322;aristotle@athens.gr;'Aristotle'") == []

def test_q3n_empty_path():
    errs = validate_uri('q3n://')
    assert len(errs) == 1
    assert 'path' in errs[0]


# file
def test_file_valid():
    assert validate_uri('file:///home/user/notes.q3n') == []

def test_file_empty_path():
    errs = validate_uri('file://')
    assert len(errs) == 1
    assert 'path' in errs[0]


def test_wikipedia_valid():
    assert validate_uri('wikipedia://Quantum_mechanics') == []
    assert validate_uri('wikipedia://fr/Paris') == []

def test_wikipedia_empty():
    errs = validate_uri('wikipedia://')
    assert len(errs) == 1
    assert 'article' in errs[0]

def test_github_valid():
    assert validate_uri('github://torvalds/linux') == []
    assert validate_uri('github://user/repo/issues/123') == []

def test_github_invalid():
    errs = validate_uri('github://')
    assert len(errs) == 1


# unknown scheme passes through
def test_unknown_scheme_passes():
    assert validate_uri('pubmed://12345678') == []


# parser still accepts invalid URIs
def test_parser_accepts_invalid_uri():
    text = '/// isbn://bad\nquote\n\\\\\\'
    entries = parse(text)
    assert len(entries) == 1


# Q3NEntry.validate delegates to validate_uri
def test_entry_validate_method():
    e = _entry('doi://10.1234/valid')
    assert e.validate() == []

def test_entry_validate_returns_errors():
    e = _entry('doi://not-a-doi')
    assert len(e.validate()) == 1
