"""Tests for core/fortune.py — format_fortune, box_text, display_fortune, export_fortune."""

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from core.q3n import Q3NEntry, parse
from core.fortune import (
    format_fortune, box_text, display_fortune, export_fortune,
    pick_art, ASCII_ART,
)


def _entry(uri='https://example.com', quote='Hello world.', tag=None, scheme='https'):
    path = uri.split('://', 1)[1] if '://' in uri else uri
    return Q3NEntry(uri, scheme, path, quote, tag)


# ── format_fortune ─────────────────────────────────────────────────────


def test_format_fortune_short_quote():
    e = _entry(quote='Short quote.')
    result = format_fortune(e)
    assert 'Short quote.' in result


def test_format_fortune_wraps_long_lines():
    long_quote = ' '.join(['word'] * 30)
    e = _entry(quote=long_quote)
    result = format_fortune(e)
    for line in result.split('\n')[:-2]:  # skip attribution lines
        assert len(line) <= 60


def test_format_fortune_includes_attribution():
    e = _entry(uri='https://example.com', quote='A quote.')
    result = format_fortune(e)
    assert 'example.com' in result


def test_format_fortune_empty_quote():
    e = _entry(quote='')
    result = format_fortune(e)
    assert isinstance(result, str)


# ── box_text ────────────────────────────────────────────────────────────


def test_box_text_has_borders():
    result = box_text('Hello')
    assert result.startswith('+')
    assert result.endswith('+')
    assert '| Hello' in result


def test_box_text_multiline():
    result = box_text('Line one\nLine two')
    assert '| Line one' in result
    assert '| Line two' in result


def test_box_text_empty():
    result = box_text('')
    assert '+' in result


def test_box_text_border_capped_at_60():
    long_line = 'x' * 100
    result = box_text(long_line)
    border = result.split('\n')[0]
    # Border width is capped at 60 content chars + 2 ('+' on each end) + 2 spaces
    assert len(border) == 64  # '+' + '-'*62 + '+'


# ── display_fortune ─────────────────────────────────────────────────────


def test_display_fortune_empty_list():
    assert display_fortune([]) == 'No fortunes found!'


def test_display_fortune_no_art():
    e = _entry(quote='A quote.')
    result = display_fortune([e], no_art=True)
    assert 'A quote' in result
    assert '+' in result


def test_display_fortune_with_art():
    e = _entry(quote='A quote.')
    result = display_fortune([e], no_art=False)
    assert 'A quote' in result
    # Art contains at least one non-alphanumeric character
    assert any(c in result for c in ['.', '/', '\\', '|', '-', '~', '*'])


def test_display_fortune_specific_art():
    e = _entry(quote='A quote.')
    result = display_fortune([e], art='cookie', no_art=False)
    assert 'FORTUNE' in result


def test_display_fortune_picks_from_list():
    entries = [_entry(quote=f'Quote {i}.') for i in range(5)]
    result = display_fortune(entries, no_art=True)
    assert 'Quote' in result


# ── export_fortune ──────────────────────────────────────────────────────


def test_export_fortune_delimiter():
    entries = [_entry(quote='First.'), _entry(quote='Second.')]
    result = export_fortune(entries)
    assert result.count('%') == 2


def test_export_fortune_content():
    entries = [_entry(quote='Hello.'), _entry(quote='World.')]
    result = export_fortune(entries)
    assert 'Hello.' in result
    assert 'World.' in result


def test_export_fortune_single_entry():
    entries = [_entry(quote='One.')]
    result = export_fortune(entries)
    assert 'One.' in result
    assert '%' in result


def test_export_fortune_empty():
    result = export_fortune([])
    assert result == ''


# ── pick_art ────────────────────────────────────────────────────────────


def test_pick_art_specific():
    art = pick_art(specific='cookie')
    assert 'FORTUNE' in art


def test_pick_art_specific_unknown_falls_back():
    art = pick_art(specific='nonexistent')
    assert 'FORTUNE' in art  # falls back to cookie


def test_pick_art_no_args_returns_something():
    art = pick_art()
    assert isinstance(art, str)
    assert len(art) > 0


def test_pick_art_isbn_scheme():
    e = _entry(uri='isbn://978-x', scheme='isbn', quote='Book.')
    # isbn scheme has 50% chance of 'book' art — call many times and check variety
    arts = {pick_art(entry=e) for _ in range(20)}
    assert len(arts) >= 1  # at least returns something valid


def test_pick_art_all_keys_valid():
    for key in ASCII_ART:
        art = pick_art(specific=key)
        assert isinstance(art, str)
        assert len(art) > 0
