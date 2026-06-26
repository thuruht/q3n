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
| `tutorial` | Interactive tutorial |
| `help [CMD]` | Show help or man page |

## GUI

Run `./bin/q3n-gui` to launch the Q3N Manager, a PySide6-based graphical browser and editor.

## URI schemes

`https://`, `http://`, `file://`, `isbn://`, `doi://`, `arxiv://`, `yt://`, `q3n://`

## Export formats

- Q3N, JSON, Markdown, HTML, Plain text, Markdown index

## License

AGPL-3.0 with Anti-Fascist Exception
