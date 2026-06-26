# Q3N Specification (v1.1)

This document provides the formal specification for the Quote Triple-Slash Notation (Q3N) format.

## Core Grammar (EBNF)

```ebnf
q3n        = "///", ws, source_uri, [ws, "///", ws, tag, ":"], ws, newline,
             quote_text,
             "\\\", newline ;
source_uri = (standard_uri | custom_uri) ;
standard_uri = scheme "://" path ;
custom_uri  = scheme "://" [author], path ;
scheme      = (letter | digit), {letter | digit | "+" | "-" | "."} ;
path        = {unreserved | escaped | delimiter} ;
tag         = {letter | digit | "/" | "-" | "_"} ;
quote_text  = {char | newline} - "\\\" ;
char        = letter | digit | symbol ;
ws          = {" " | "\t"} ;
newline     = "\n" | "\r\n" ;
```

## Regex Pattern

```regex
^\/\/\/[ \t]+(?P<uri>.+?)(?:[ \t]+\/\/\/[ \t]+(?P<tag>[^:\s]+):)?[ \t]*$
```

The closing delimiter is `\\\` on its own line (matched by `^\\\\\\[ \t]*$`).

## URI Schemes

| Scheme       | Format Example                                    | Use Case                   |
|--------------|---------------------------------------------------|----------------------------|
| `https://`   | `https://example.com/page#section`               | Web sources                |
| `http://`    | `http://example.com/page`                        | Web sources (unencrypted)  |
| `file://`    | `file:///path/to/notes.txt#line=5`               | Local files                |
| `q3n://`     | `q3n://handle:id;email;'Name'`                   | People / contacts          |
| `isbn://`    | `isbn://978-0-13-468599-1;'Title';'Author';2024` | Books                      |
| `doi://`     | `doi://10.1234/abcd.567`                         | Academic papers            |
| `arxiv://`   | `arxiv://2305.12345`                             | arXiv preprints            |
| `pubmed://`  | `pubmed://12345678`                              | PubMed articles            |
| `yt://`      | `yt://dQw4w9WgXcQ` or `yt://watch?v=ID&t=42`    | YouTube videos             |
| `spotify://` | `spotify://track:4cOdK2wGLETKBW3PvgPWqT`        | Music tracks               |
| `orcid://`   | `orcid://0000-0002-1825-0097`                    | Researcher identifiers     |

### Scheme-specific payload formats

**`isbn://`** — semicolon-separated fields: `isbn://ISBN;'Title';'Author';Year`

**`q3n://`** — semicolon-separated fields: `q3n://handle:id;email@domain;'Full Name'`

**`yt://`** — bare video ID or query string: `yt://VIDEO_ID` or `yt://VIDEO_ID?t=SECONDS`

**`pubmed://`** — PubMed article ID (PMID): `pubmed://12345678`

**`orcid://`** — ORCID iD in hyphenated format: `orcid://0000-0002-1825-0097`

**`spotify://`** — Spotify URI path: `spotify://track:ID` or `spotify://album:ID`

## Tags

Tags are optional slash-delimited hierarchies appended to the opening line:

```
/// https://example.com/article /// cite/article:
```

Recommended conventions: `cite/article`, `cite/book`, `cite/interview`, `note/idea`, `note/research`, `note/summary`.

## File Detection

A file is recognised as Q3N if any of:
- Extension is `.q3n`, `.q3nt`, `.quotation`, or `.quotes`
- First line is `#!q3n-format`
- Content contains a line matching `^///\s+\S+`

## Validation Rules

1. Must preserve whitespace exactly within quote blocks.
2. Must support UTF-8 encoding.
3. Entries without a closing `\\\` marker are silently dropped by parsers.
4. The maximum recommended size for a single quote block is 65,536 bytes.

## Version History

- v1.0: Initial specification
- v1.1: Added `pubmed://`, `spotify://`, `orcid://` schemes; formalised tag syntax
