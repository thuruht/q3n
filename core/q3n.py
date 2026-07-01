#!/usr/bin/env python3
import re
import sys
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs


SCHEME_REGISTRY = {
    'https': 'web',
    'http': 'web',
    'q3n': 'person',
    'isbn': 'book',
    'doi': 'academic',
    'arxiv': 'academic',
    'pubmed': 'academic',
    'orcid': 'person',
    'file': 'file',
    'yt': 'media',
    'youtube': 'media',
    'spotify': 'media',
    'osm': 'map',
    'geo': 'map',
    'overpass': 'map',
    'wikipedia': 'web',
    'github': 'web',
}

RECOGNIZED_EXTENSIONS = {'.q3n', '.q3nt', '.quotation', '.quotes'}


def detect_content_type(quote):
    """Classify quote body content type: 'json', 'code', or 'text'."""
    stripped = quote.strip()
    if not stripped:
        return 'text'
    if stripped.startswith('{') and stripped.endswith('}'):
        try:
            json.loads(stripped)
            return 'json'
        except (json.JSONDecodeError, ValueError):
            pass
    if stripped.startswith('```') or stripped.startswith('def ') \
            or stripped.startswith('class ') or stripped.startswith('import '):
        return 'code'
    lines = stripped.split('\n')
    code_keywords = {'def ', 'class ', 'import ', 'from ', 'return ',
                     'if __name__', '#include', 'fn ', 'func ', 'function ',
                     'let ', 'const ', 'var ', 'print('}
    code_lines = sum(1 for line in lines if any(line.startswith(k) for k in code_keywords))
    if len(lines) > 2 and code_lines / len(lines) > 0.3:
        return 'code'
    return 'text'


def parse_scheme(uri):
    if '://' in uri:
        return uri.split('://', 1)
    if ':' in uri:
        scheme = uri.split(':', 1)[0].lower()
        if scheme.isalpha():
            return scheme, uri.split(':', 1)[1]
    return '', uri


def parse_q3n_uri(uri):
    parts = uri.replace('q3n://', '').split(';')
    result = {'type': 'person'}
    if parts and ':' in parts[0]:
        handle, user_id = parts[0].split(':', 1)
        result['handle'] = handle
        result['id'] = user_id.lstrip('@')
    if len(parts) > 1:
        result['email'] = parts[1]
    if len(parts) > 2:
        name = parts[2].strip("'")
        result['name'] = name
    return result


def parse_isbn_uri(uri):
    parts = uri.replace('isbn://', '').split(';')
    result = {'type': 'book', 'isbn': parts[0]}
    if len(parts) > 1:
        result['title'] = parts[1].strip("'")
    if len(parts) > 2:
        result['author'] = parts[2].strip("'")
    if len(parts) > 3:
        try:
            result['year'] = int(parts[3])
        except ValueError:
            result['year'] = parts[3]
    return result


def parse_doi_uri(uri):
    return {'type': 'academic', 'doi': uri.replace('doi://', '')}


def parse_arxiv_uri(uri):
    return {'type': 'academic', 'arxiv_id': uri.replace('arxiv://', '')}


def parse_pubmed_uri(uri):
    return {'type': 'academic', 'pmid': uri.replace('pubmed://', '')}


def parse_orcid_uri(uri):
    return {'type': 'person', 'orcid': uri.replace('orcid://', '')}


def parse_spotify_uri(uri):
    rest = uri.replace('spotify://', '')
    result = {'type': 'media', 'platform': 'spotify'}
    if ':' in rest:
        kind, item_id = rest.split(':', 1)
        result['kind'] = kind
        result['id'] = item_id
    else:
        result['id'] = rest
    return result


def parse_yt_uri(uri):
    rest = uri.replace('yt://', '')
    result = {'type': 'media', 'platform': 'youtube'}
    if '?' in rest:
        base, qs = rest.split('?', 1)
        params = parse_qs(qs)
        if 'v' in params:
            result['video_id'] = params['v'][0]
        if 't' in params:
            try:
                result['timestamp'] = int(params['t'][0])
            except ValueError:
                result['timestamp'] = params['t'][0]
        if base and not result.get('video_id'):
            result['video_id'] = base
    else:
        result['video_id'] = rest
    return result


def parse_web_uri(uri):
    parsed = urlparse(uri)
    result = {'domain': parsed.netloc}
    if parsed.fragment:
        result['fragment'] = parsed.fragment
    if parsed.query:
        try:
            result['query_params'] = parse_qs(parsed.query)
        except Exception:
            result['query_string'] = parsed.query
    return result


def parse_file_uri(uri):
    parsed = urlparse(uri)
    result = {'path': parsed.path}
    if parsed.fragment and 'line=' in parsed.fragment:
        try:
            result['line'] = int(parsed.fragment.split('line=')[1])
        except (ValueError, IndexError):
            pass
    return result


def parse_osm_uri(uri):
    path = uri.replace('osm://', '')
    parts = path.split('/', 1)
    obj_type = parts[0] if parts else 'node'
    obj_id = parts[1] if len(parts) > 1 else ''
    base = 'https://www.openstreetmap.org'
    api = 'https://api.openstreetmap.org/api/0.6'
    return {
        'type': obj_type,
        'id': obj_id,
        'browse_url': f'{base}/{obj_type}/{obj_id}',
        'api_url': f'{api}/{obj_type}/{obj_id}',
    }


def parse_geo_uri(uri):
    parsed = urlparse(uri)
    coord_str = parsed.path
    result = {}
    try:
        lat_str, lon_str = coord_str.split(',', 1)
        result['lat'] = float(lat_str)
        result['lon'] = float(lon_str)
    except (ValueError, AttributeError):
        return result
    zoom = None
    if parsed.query:
        for part in parsed.query.split('&'):
            if part.startswith('z='):
                try:
                    zoom = int(part[2:])
                except ValueError:
                    pass
    if zoom is not None:
        result['zoom'] = zoom
    z_param = f'&zoom={zoom}' if zoom is not None else '&zoom=14'
    result['map_url'] = (
        f'https://www.openstreetmap.org/?mlat={result["lat"]}'
        f'&mlon={result["lon"]}{z_param}'
    )
    return result


def parse_overpass_uri(uri):
    query = uri.replace('overpass://', '')
    from urllib.parse import quote as url_quote
    return {
        'query': query,
        'api_url': f'https://overpass-api.de/api/interpreter?data={url_quote(query)}',
    }


def parse_wikipedia_uri(uri):
    rest = uri.replace('wikipedia://', '')
    parts = rest.split('/', 1)
    lang = None
    article = rest
    if '/' in rest and len(parts[0]) == 2:
        lang = parts[0]
        article = parts[1]
    browse_url = (
        f'https://{lang}.wikipedia.org/wiki/{article}'
        if lang else f'https://en.wikipedia.org/wiki/{article}'
    )
    return {
        'type': 'web',
        'article': article,
        'lang': lang or 'en',
        'browse_url': browse_url,
    }


def parse_github_uri(uri):
    rest = uri.replace('github://', '')
    parts = rest.split('/')
    owner = parts[0] if len(parts) >= 1 else ''
    repo = parts[1] if len(parts) >= 2 else ''
    kind = None
    kind_id = None
    label = f'{owner}/{repo}'
    if len(parts) >= 4:
        kind = parts[2]
        kind_id = parts[3]
        label = f'{owner}/{repo}/{kind}/{kind_id}'
    browse_url = f'https://github.com/{owner}/{repo}'
    if kind:
        browse_url += f'/{kind}/{kind_id}'
    return {
        'type': 'web',
        'platform': 'github',
        'owner': owner,
        'repo': repo,
        'kind': kind,
        'id': kind_id,
        'label': label,
        'browse_url': browse_url,
    }


URI_PARSERS = {
    'q3n': parse_q3n_uri,
    'isbn': parse_isbn_uri,
    'doi': parse_doi_uri,
    'arxiv': parse_arxiv_uri,
    'pubmed': parse_pubmed_uri,
    'orcid': parse_orcid_uri,
    'spotify': parse_spotify_uri,
    'yt': parse_yt_uri,
    'youtube': parse_yt_uri,
    'https': parse_web_uri,
    'http': parse_web_uri,
    'file': parse_file_uri,
    'osm': parse_osm_uri,
    'geo': parse_geo_uri,
    'overpass': parse_overpass_uri,
    'wikipedia': parse_wikipedia_uri,
    'github': parse_github_uri,
}


def _isbn13_valid(digits: str) -> bool:
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    return total % 10 == 0


def _isbn10_valid(digits: str) -> bool:
    if len(digits) != 10:
        return False
    total = 0
    for i, c in enumerate(digits.upper()):
        if c == 'X':
            if i != 9:
                return False
            total += 10
        elif c.isdigit():
            total += int(c) * (10 - i)
        else:
            return False
    return total % 11 == 0


def validate_uri(uri: str) -> list:
    """Return list of validation error strings. Empty list means valid."""
    errors = []
    if '://' not in uri:
        errors.append('missing URI scheme')
        return errors
    scheme = uri.split('://')[0].lower()

    if scheme in ('https', 'http'):
        parsed = urlparse(uri)
        if not parsed.netloc:
            errors.append('missing host in URL')

    elif scheme == 'isbn':
        raw = uri.replace('isbn://', '').split(';')[0]
        digits = raw.replace('-', '').replace(' ', '')
        if len(digits) == 13:
            if not _isbn13_valid(digits):
                errors.append('invalid ISBN-13 checksum')
        elif len(digits) == 10:
            if not _isbn10_valid(digits):
                errors.append('invalid ISBN-10 checksum')
        else:
            errors.append(f'invalid ISBN length: {len(digits)} (expected 10 or 13)')

    elif scheme == 'doi':
        doi = uri.replace('doi://', '')
        if not re.match(r'^10\.\d{4,}/\S+', doi):
            errors.append('DOI must match 10.XXXX/... format')

    elif scheme == 'arxiv':
        arxiv_id = uri.replace('arxiv://', '')
        if not (re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', arxiv_id) or
                re.match(r'^[a-z][a-z\-]*(\.[A-Z]{2})?/\d{7}$', arxiv_id)):
            errors.append(f'invalid arXiv ID format: {arxiv_id!r}')

    elif scheme == 'yt':
        meta = parse_yt_uri(uri)
        vid = meta.get('video_id', '')
        if len(vid) != 11:
            errors.append(f'YouTube video ID must be 11 chars, got {len(vid)!r}')

    elif scheme == 'q3n':
        path = uri.replace('q3n://', '').split(';')[0].strip()
        if not path:
            errors.append('q3n URI must have a non-empty path')

    elif scheme == 'file':
        path = urlparse(uri).path
        if not path:
            errors.append('file URI must have a non-empty path')

    elif scheme == 'wikipedia':
        article = uri.replace('wikipedia://', '').split('/', 1)[-1] if '/' in uri.replace('wikipedia://', '', 1) else uri.replace('wikipedia://', '')
        if not article:
            errors.append('wikipedia URI must have a non-empty article title')

    elif scheme == 'github':
        parts = uri.replace('github://', '').split('/')
        if len(parts) < 2 or not parts[0] or not parts[1]:
            errors.append('github URI must have owner/repo format')

    return errors


def resolve_uri(uri_data):
    """Return a human-readable source attribution string."""
    scheme = uri_data.get('scheme', '')
    meta = uri_data.get('meta', {})

    if scheme == 'q3n':
        if 'name' in meta:
            return f"— {meta['name']}"
        if 'handle' in meta:
            return f"— @{meta['handle']}"
        if 'email' in meta:
            return f"— {meta['email']}"
    elif scheme == 'isbn':
        parts = []
        if 'author' in meta:
            parts.append(meta['author'])
        if 'title' in meta:
            parts.append(f'"{meta["title"]}"')
        if 'year' in meta:
            parts.append(f'({meta["year"]})')
        if parts:
            return f"— {', '.join(parts)}"
    elif scheme in ('doi', 'arxiv', 'pubmed'):
        return f"— Academic paper ({scheme})"
    elif scheme == 'orcid':
        if 'orcid' in meta:
            return f"— ORCID {meta['orcid']}"
    elif scheme == 'spotify':
        kind = meta.get('kind', 'track')
        return f"— Spotify {kind}"
    elif scheme in ('https', 'http'):
        if 'domain' in meta:
            return f"— {meta['domain']}"
    elif scheme in ('yt', 'youtube'):
        return f"— YouTube"
    elif scheme == 'wikipedia':
        if 'article' in meta:
            lang = meta.get('lang', 'en').upper()
            article = meta['article'].replace('_', ' ')
            return f"— Wikipedia ({lang}): {article}"
    elif scheme == 'github':
        if 'label' in meta:
            return f"— GitHub: {meta['label']}"
    return f"— {uri_data.get('uri', '')}"


class Q3NEntry:
    def __init__(self, uri, scheme, path, quote, tag=None):
        self.uri = uri
        self.scheme = scheme
        self.path = path
        self.quote = quote.rstrip('\n')
        self.tag = tag.rstrip(':') if tag else None

    def as_dict(self):
        d = {
            'uri': self.uri,
            'scheme': self.scheme,
            'path': self.path,
            'quote': self.quote,
        }
        if self.tag:
            d['tag'] = self.tag
        derived = self._derive()
        d.update(derived)
        return d

    def _derive(self):
        r = {}
        parser = URI_PARSERS.get(self.scheme)
        if parser:
            try:
                r['meta'] = parser(self.uri)
            except (ValueError, AttributeError, TypeError, KeyError):
                pass
        if 'meta' not in r:
            if self.scheme in ('https', 'http'):
                parsed = urlparse(self.uri)
                r['meta'] = {'domain': parsed.netloc}
            elif self.scheme == 'file':
                parsed = urlparse(self.uri)
                r['meta'] = {'path': parsed.path}
        if self.scheme in SCHEME_REGISTRY:
            r['category'] = SCHEME_REGISTRY[self.scheme]
        r['content_type'] = detect_content_type(self.quote)
        return r

    def attribution(self):
        """Human-readable source string."""
        meta = self._derive().get('meta', {})
        uri_data = {
            'uri': self.uri,
            'scheme': self.scheme,
            'meta': meta,
        }
        return resolve_uri(uri_data)

    def validate(self) -> list:
        return validate_uri(self.uri)

    def __repr__(self):
        preview = self.quote[:50] + '...' if len(self.quote) > 50 else self.quote
        return f"<Q3NEntry {self.scheme}://{self.path[:40]} — {preview}>"


Q3N_START = re.compile(
    r'^///[ \t]+(?P<uri>.+?)'
    r'(?:[ \t]+///[ \t]+(?P<tag>[^:\s]+):)?'
    r'[ \t]*$'
)
Q3N_END = re.compile(r'^\\\\\\[ \t]*$')


def parse(text):
    r"""
    Parse Q3N formatted text into structured entries.

    Recognizes the format:
        /// <source_uri> [/// <tag>:]
        <content>
        \\\   (triple backslash closes the block)

    Uses line-by-line parsing (no backtracking) for safety on large files.
    Entries without a closing \\\ marker are silently dropped.
    """
    entries = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        m = Q3N_START.match(line)
        if m:
            uri = m.group('uri')
            tag = m.group('tag')
            quote_lines = []
            i += 1
            closed = False
            while i < len(lines):
                if Q3N_END.match(lines[i]):
                    closed = True
                    break
                # Allow \\\ at end of the last quote line (not just own line)
                if lines[i].rstrip().endswith('\\\\\\'):
                    quote_lines.append(lines[i].rstrip()[:-3])
                    closed = True
                    break
                quote_lines.append(lines[i])
                i += 1
            if closed:
                quote = '\n'.join(quote_lines).rstrip('\n')
                scheme, path = parse_scheme(uri)
                entries.append(Q3NEntry(uri, scheme, path, quote, tag))
        i += 1
    return entries


def parse_file(path):
    return parse(Path(path).read_text(encoding='utf-8'))


def serialize(entries, header=True):
    lines = []
    if header:
        lines.append('#!q3n-format')
        lines.append('')
    for e in entries:
        tag_part = f' /// {e.tag}:' if e.tag else ''
        lines.append(f'/// {e.uri}{tag_part}')
        lines.append(e.quote)
        lines.append('\\\\\\')
        lines.append('')
    return '\n'.join(lines)


def serialize_file(entries, path):
    Path(path).write_text(serialize(entries), encoding='utf-8')


def _entry_url(entry):
    """Best browser-navigable URL for an entry, or None if not linkable."""
    if entry.uri.startswith(('https://', 'http://')):
        return entry.uri
    meta = entry.as_dict().get('meta', {})
    return meta.get('browse_url') or meta.get('map_url') or None


def export_json(entries):
    return json.dumps([e.as_dict() for e in entries], indent=2)


def export_markdown(entries):
    lines = ['# Q3N Collection\n']
    for i, e in enumerate(entries):
        lines.append(f'## Entry {i+1}')
        if e.tag:
            lines.append(f'**Tag:** {e.tag}')
        url = _entry_url(e)
        src = f'[{e.uri}]({url})' if url else e.uri
        lines.append(f'**Source:** {src}')
        lines.append('')
        for paragraph in e.quote.split('\n'):
            if paragraph.strip():
                lines.append(f'> {paragraph}')
            else:
                lines.append('>')
        lines.append('')
        lines.append('---')
        lines.append('')
    return '\n'.join(lines)


def export_html(entries):
    parts = ['<!DOCTYPE html><html><head><meta charset="utf-8">'
             '<title>Q3N Collection</title>'
             '<style>body{font-family:sans-serif;max-width:700px;margin:auto;padding:2em}'
             '.entry{margin:2em 0;padding:1em;border-left:3px solid #ccc}'
             '.uri{color:#888;font-size:0.9em}.tag{display:inline-block;'
             'background:#e0e0e0;padding:2px 8px;border-radius:3px;font-size:0.8em}'
             'blockquote{margin:1em 0;padding:0 1em;border-left:3px solid #999;color:#333}'
             '</style></head><body>']
    parts.append('<h1>Q3N Collection</h1>')
    for e in entries:
        parts.append('<div class="entry">')
        url = _entry_url(e)
        uri_html = (f'<a href="{url}" target="_blank">{e.uri}</a>' if url else e.uri)
        parts.append(f'<div class="uri">{uri_html}</div>')
        if e.tag:
            parts.append(f'<span class="tag">{e.tag}</span>')
        parts.append('<blockquote>')
        for line in e.quote.split('\n'):
            parts.append(f'{line}<br>' if line else '<br>')
        parts.append('</blockquote>')
        parts.append('</div>')
    parts.append('</body></html>')
    return '\n'.join(parts)


def export_plaintext(entries):
    lines = []
    for i, e in enumerate(entries):
        if i > 0:
            lines.append('')
            lines.append('---')
            lines.append('')
        tag_str = f' [{e.tag}]' if e.tag else ''
        lines.append(f'Source: {e.uri}{tag_str}')
        lines.append('')
        lines.append(e.quote)
    return '\n'.join(lines)


def generate_index(entries):
    lines = ['# Q3N Index\n']
    lines.append(f'Total entries: {len(entries)}\n')
    lines.append('| # | URI | Tag | Preview |')
    lines.append('|---|-----|-----|---------|')
    for i, e in enumerate(entries):
        preview = e.quote[:60].replace('\n', ' ')
        tag_str = e.tag or ''
        uri_short = e.uri[:60] + '...' if len(e.uri) > 60 else e.uri
        lines.append(f'| {i+1} | {uri_short} | {tag_str} | {preview} |')
    lines.append('')
    counts = {}
    for e in entries:
        t = e.tag or '(none)'
        counts[t] = counts.get(t, 0) + 1
    lines.append('## By Tag\n')
    for tag, count in sorted(counts.items()):
        lines.append(f'- {tag}: {count}')
    return '\n'.join(lines)


def import_json(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    entries = []
    for item in data:
        uri = item.get('uri', '')
        quote = item.get('quote', '')
        tag = item.get('tag')
        scheme, path_val = parse_scheme(uri)
        entries.append(Q3NEntry(uri, scheme, path_val, quote, tag))
    return entries


def export_file(entries, path, fmt='q3n'):
    path = Path(path)
    if fmt == 'q3n':
        serialize_file(entries, path)
    elif fmt == 'json':
        path.write_text(export_json(entries), encoding='utf-8')
    elif fmt == 'md':
        path.write_text(export_markdown(entries), encoding='utf-8')
    elif fmt == 'html':
        path.write_text(export_html(entries), encoding='utf-8')
    elif fmt == 'txt':
        path.write_text(export_plaintext(entries), encoding='utf-8')
    elif fmt == 'index':
        path.write_text(generate_index(entries), encoding='utf-8')
    elif fmt == 'fortune':
        from core.fortune import export_fortune
        text = export_fortune(entries)
        path.write_text(text, encoding='utf-8')
    elif fmt == 'anki':
        from app.plugins.anki.export import export_anki_csv
        text = export_anki_csv(entries)
        path.write_text(text, encoding='utf-8')


def detect(path):
    p = Path(path)
    if not p.exists():
        return False
    if p.suffix in RECOGNIZED_EXTENSIONS:
        return True
    try:
        from core.config import get_config
        max_bytes = get_config()['core'].getint('scan_max_bytes', 10_485_760)
        if p.stat().st_size > max_bytes:
            return False
        text = p.read_text(encoding='utf-8')
        if text.startswith('#!q3n-format'):
            return True
        if re.search(r'^///\s+\S+', text, re.MULTILINE):
            return True
    except (OSError, UnicodeDecodeError, re.error):
        pass
    return False


def list_entries(directory='.'):
    results = []
    for p in Path(directory).rglob('*'):
        if p.is_file() and p.suffix in RECOGNIZED_EXTENSIONS and detect(p):
            try:
                entries = parse_file(p)
                if entries:
                    results.append((p, entries))
            except (OSError, UnicodeDecodeError, ValueError):
                pass
    return results
