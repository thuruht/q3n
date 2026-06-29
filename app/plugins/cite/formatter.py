from core.q3n import Q3NEntry


def format_citation(entry: Q3NEntry, style: str) -> str:
    """Format entry as a citation. style: 'mla'|'apa'|'chicago'|'bibtex'"""
    d = entry.as_dict()
    meta = d.get('meta', {})
    scheme = entry.scheme
    if style == 'mla':
        return _mla(entry, meta, scheme)
    elif style == 'apa':
        return _apa(entry, meta, scheme)
    elif style == 'chicago':
        return _chicago(entry, meta, scheme)
    elif style == 'bibtex':
        return _bibtex(entry, meta, scheme)
    return entry.uri


# ── MLA 9 ────────────────────────────────────────────────────────────

def _mla(entry, meta, scheme):
    if scheme == 'isbn':
        author = _fmt_author_mla(meta.get('author', ''))
        title = meta.get('title', '[n.t.]').replace('_', ' ')
        year = meta.get('year', '[n.d.]')
        publisher = meta.get('publisher', '[n.p.]')
        return f'{author} *{title}*. {publisher}, {year}.'

    elif scheme == 'doi':
        doi = meta.get('doi', entry.uri.replace('doi://', ''))
        return f'[n.a.] "[n.t.]" *[n.pub.]*, https://doi.org/{doi}.'

    elif scheme == 'arxiv':
        arxiv_id = meta.get('arxiv_id', entry.uri.replace('arxiv://', ''))
        return f'[n.a.] "[n.t.]" arXiv:{arxiv_id}.'

    elif scheme in ('https', 'http'):
        domain = meta.get('domain', entry.uri)
        return f'[n.a.] "[n.t.]" *{domain}*, {entry.uri}.'

    elif scheme in ('yt', 'youtube'):
        vid = meta.get('video_id', '')
        return f'[n.a.] "YouTube video." *YouTube*, https://youtu.be/{vid}.'

    elif scheme == 'q3n':
        name = meta.get('name', meta.get('handle', meta.get('email', entry.uri)))
        return f'{name}.'

    return entry.uri


def _fmt_author_mla(raw: str) -> str:
    raw = raw.replace('_', ' ').strip()
    if not raw:
        return '[n.a.]'
    parts = raw.split()
    if len(parts) >= 2:
        return f'{parts[-1]}, {" ".join(parts[:-1])}'
    return raw


# ── APA 7 ────────────────────────────────────────────────────────────

def _apa(entry, meta, scheme):
    if scheme == 'isbn':
        author = _fmt_author_apa(meta.get('author', ''))
        year = meta.get('year', '')
        year_str = f'({year})' if year else '(n.d.)'
        title = meta.get('title', '[n.t.]').replace('_', ' ')
        publisher = meta.get('publisher', '[n.p.]')
        return f'{author} {year_str}. *{title}*. {publisher}.'

    elif scheme == 'doi':
        doi = meta.get('doi', entry.uri.replace('doi://', ''))
        return f'[n.a.] (n.d.). [n.t.]. https://doi.org/{doi}'

    elif scheme == 'arxiv':
        arxiv_id = meta.get('arxiv_id', entry.uri.replace('arxiv://', ''))
        return f'[n.a.] (n.d.). [n.t.]. arXiv:{arxiv_id}'

    elif scheme in ('https', 'http'):
        return f'[n.a.] (n.d.). [n.t.]. {entry.uri}'

    return entry.uri


def _fmt_author_apa(raw: str) -> str:
    raw = raw.replace('_', ' ').strip()
    if not raw:
        return ''
    parts = raw.split()
    if len(parts) >= 2:
        initials = ' '.join(p[0] + '.' for p in parts[:-1])
        return f'{parts[-1]}, {initials}'
    return raw


# ── Chicago 17 author-date ───────────────────────────────────────────

def _chicago(entry, meta, scheme):
    if scheme == 'isbn':
        author = _fmt_author_chicago(meta.get('author', ''))
        year = meta.get('year', '[n.d.]')
        title = meta.get('title', '[n.t.]').replace('_', ' ')
        publisher = meta.get('publisher', '[n.p.]')
        return f'{author} {year}. *{title}*. {publisher}.'

    elif scheme == 'doi':
        doi = meta.get('doi', entry.uri.replace('doi://', ''))
        return f'[n.a.] [n.d.] "[n.t.]" https://doi.org/{doi}.'

    elif scheme == 'arxiv':
        arxiv_id = meta.get('arxiv_id', entry.uri.replace('arxiv://', ''))
        return f'[n.a.] [n.d.] "[n.t.]" arXiv:{arxiv_id}.'

    elif scheme in ('https', 'http'):
        return f'[n.a.] [n.d.] "[n.t.]" {entry.uri}.'

    return entry.uri


def _fmt_author_chicago(raw: str) -> str:
    raw = raw.replace('_', ' ').strip()
    if not raw:
        return '[n.a.]'
    parts = raw.split()
    if len(parts) >= 2:
        return f'{parts[-1]}, {" ".join(parts[:-1])}'
    return raw


# ── BibTeX ───────────────────────────────────────────────────────────

def _bibtex(entry, meta, scheme):
    author = meta.get('author', '').replace('_', ' ').strip() or 'Unknown'
    year = str(meta.get('year', '')) or 'nd'
    key_base = (author.split()[-1] if author != 'Unknown' else 'unknown').lower()
    key = f'{key_base}{year}'

    if scheme == 'isbn':
        title = meta.get('title', '').replace('_', ' ')
        isbn = meta.get('isbn', entry.uri.replace('isbn://', '').split(';')[0])
        publisher = meta.get('publisher', '')
        lines = [
            f'@book{{{key},',
            f'  author    = {{{author}}},',
            f'  title     = {{{title}}},',
        ]
        if publisher:
            lines.append(f'  publisher = {{{publisher}}},')
        if year != 'nd':
            lines.append(f'  year      = {{{year}}},')
        lines.append(f'  isbn      = {{{isbn}}}')
        lines.append('}')
        return '\n'.join(lines)

    elif scheme == 'doi':
        doi = meta.get('doi', entry.uri.replace('doi://', ''))
        return (f'@article{{{key_base}doi,\n'
                f'  doi  = {{{doi}}}\n}}')

    elif scheme == 'arxiv':
        arxiv_id = meta.get('arxiv_id', entry.uri.replace('arxiv://', ''))
        return (f'@misc{{{key_base}arxiv,\n'
                f'  note = {{arXiv:{arxiv_id}}}\n}}')

    return f'@misc{{{key_base},\n  howpublished = {{{entry.uri}}}\n}}'
