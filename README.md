# Q3N — Quote Triple-Slash Notation

A plain-text file format and toolchain for storing quotations, citations, and annotated excerpts with source URIs.

## Quick start

```bash
# Install dependencies
pip install pyside6

# Run from repo
./tools/q3n --help          # CLI
./bin/q3n-gui               # GUI

# Or install locally
pip install -e .
q3n --help
q3n-gui
```

## The format

Q3N files use a simple delimiter notation:

```
/// https://example.com/article /// cite/article:
The quoted text goes here.
Multiple paragraphs are fine.
\\\
```

- Open with `/// <source_uri> [/// <tag>:]`
- Content in the middle (any text, multiple lines)
- Close with `\\\` on its own line
- Optional `#!q3n-format` header identifies the file

## CLI commands

| Command | Description |
|---------|-------------|
| `show FILE [n]` | Display entries |
| `list [DIR]` | List entries across files |
| `create FILE` | Interactive entry creation |
| `edit FILE [n]` | Edit an entry |
| `search PATTERN [DIR]` | Search entry text |
| `stats [DIR]` | Show collection statistics |
| `export FILE -o OUT -f FMT` | Export entries |
| `import SRC DEST` | Import entries |
| `index [DIR]` | Generate markdown index |
| `init FILE` | Create empty Q3N file |
| `fortune [DIR]` | Display random quote as fortune |
| `validate FILE` | Validate URIs in a Q3N file |
| `cite FILE [--style STYLE]` | Format entries as citations (MLA/APA/Chicago/BibTeX) |
| `run PLUGIN [FILE]` | Run a plugin standalone |
| `tutorial` | Interactive tutorial |
| `help [CMD]` | Show help or man page |

## GUI

Run `./bin/q3n-gui` to launch the Q3N Manager, a PySide6-based graphical browser and editor.

Features: regex search (Ctrl+Shift+F), directory mode (File → Open Directory), tag/scheme filtering, entry wizard, export to all formats, statistics (F5), preferences, tutorial (F1), Fortune and Cite plugin panels.

## URI schemes

`https://`, `http://`, `file://`, `isbn://`, `doi://`, `arxiv://`, `pubmed://`, `yt://`, `spotify://`, `orcid://`, `q3n://`, `wikipedia://`, `github://`, `osm://`, `geo:`, `overpass://`

## Export formats

Q3N, JSON, Markdown, HTML, Plain text, Markdown index, Fortune, Anki CSV (`-f anki`)

## License

AGPL-3.0 with Anti-Fascist Exception
