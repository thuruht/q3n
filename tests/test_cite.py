import pytest
from core.q3n import parse


def _entry(uri_line, quote='Test quote.'):
    text = f'/// {uri_line}\n{quote}\n\\\\\\'
    return parse(text)[0]


@pytest.fixture
def isbn_entry():
    return _entry("isbn://978-0-13-468599-1;The_Book;Jane_Doe;1999 /// cite/book:")

@pytest.fixture
def doi_entry():
    return _entry("doi://10.1126/science.187.4176.433")

@pytest.fixture
def arxiv_entry():
    return _entry("arxiv://2301.00001")

@pytest.fixture
def https_entry():
    return _entry("https://example.com/article")

@pytest.fixture
def yt_entry():
    return _entry("yt://dQw4w9WgXcQ")

@pytest.fixture
def q3n_entry():
    return _entry("q3n://grace:@hopper;grace@navy.mil;'Grace Hopper'")


from app.plugins.cite.formatter import format_citation


class TestMLA:
    def test_isbn(self, isbn_entry):
        result = format_citation(isbn_entry, 'mla')
        assert 'Doe, Jane' in result or 'Jane_Doe' in result
        assert 'The Book' in result or 'The_Book' in result
        assert '1999' in result

    def test_doi(self, doi_entry):
        result = format_citation(doi_entry, 'mla')
        assert '10.1126' in result

    def test_arxiv(self, arxiv_entry):
        result = format_citation(arxiv_entry, 'mla')
        assert '2301.00001' in result

    def test_https(self, https_entry):
        result = format_citation(https_entry, 'mla')
        assert 'example.com' in result

    def test_yt(self, yt_entry):
        result = format_citation(yt_entry, 'mla')
        assert 'YouTube' in result or 'dQw4w9WgXcQ' in result

    def test_q3n(self, q3n_entry):
        result = format_citation(q3n_entry, 'mla')
        assert 'Grace Hopper' in result or 'grace' in result.lower()


class TestAPA:
    def test_isbn(self, isbn_entry):
        result = format_citation(isbn_entry, 'apa')
        assert '1999' in result

    def test_doi(self, doi_entry):
        result = format_citation(doi_entry, 'apa')
        assert 'https://doi.org/10.1126' in result

    def test_arxiv(self, arxiv_entry):
        result = format_citation(arxiv_entry, 'apa')
        assert '2301.00001' in result

    def test_https(self, https_entry):
        result = format_citation(https_entry, 'apa')
        assert 'example.com' in result


class TestChicago:
    def test_isbn(self, isbn_entry):
        result = format_citation(isbn_entry, 'chicago')
        assert '1999' in result

    def test_doi(self, doi_entry):
        result = format_citation(doi_entry, 'chicago')
        assert '10.1126' in result

    def test_arxiv(self, arxiv_entry):
        result = format_citation(arxiv_entry, 'chicago')
        assert '2301.00001' in result

    def test_https(self, https_entry):
        result = format_citation(https_entry, 'chicago')
        assert 'example.com' in result


class TestBibTeX:
    def test_isbn(self, isbn_entry):
        result = format_citation(isbn_entry, 'bibtex')
        assert result.startswith('@book{')
        assert 'isbn' in result
        assert '978' in result

    def test_doi(self, doi_entry):
        result = format_citation(doi_entry, 'bibtex')
        assert result.startswith('@article{')
        assert 'doi' in result

    def test_arxiv(self, arxiv_entry):
        result = format_citation(arxiv_entry, 'bibtex')
        assert result.startswith('@misc{')
        assert '2301.00001' in result


class TestGracefulDegradation:
    def test_missing_author_mla(self):
        e = _entry('isbn://978-0-13-468599-1;OnlyTitle;;1999')
        result = format_citation(e, 'mla')
        assert '[n.a.]' in result

    def test_missing_year_apa(self):
        e = _entry('isbn://978-0-13-468599-1;Title;Author;')
        result = format_citation(e, 'apa')
        assert 'n.d.' in result

    def test_all_formats_return_string(self, isbn_entry):
        for style in ('mla', 'apa', 'chicago', 'bibtex'):
            result = format_citation(isbn_entry, style)
            assert isinstance(result, str)
            assert len(result) > 0
