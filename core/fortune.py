import random
from pathlib import Path


ASCII_ART = {
    "cookie": r"""
    .-~~~-.
   /       \
  |  FORTUNE |
   \       /
    `-...-'
""",
    "penguin": r"""
   .-.
  (o o)
  (   )
  -"-"-
""",
    "book": r"""
    .--.
   |o_o |
   |:_/ |
  //   \ \
 (|     | )
/'\_   _/`\
\___)=(___/
""",
    "lightbulb": r"""
     .-.
    (o o)
    |   |
    '~~~'
     /|\
    / | \
   /  |  \
""",
    "computer": r"""
    .---.
   | .-. |
   | |~| |
   | '-' |
    `---'
""",
    "star": r"""
      .
     /|\
    /*|*\
   /__|__\
  /__|*|__\
     |*|
     |_|
""",
    "cat": r"""
 /\_/\
( o.o )
 > ^ <
""",
    "brain": r"""
    _---~~(~~-_.
  _{        )   )
 ,   ) -~~- ( ,-' )_
(  `-,_..`., )-- '_,)
( ` _)  (  -~( -_ `,  }
(_-  _  ~_-~~~~`,  ,' )
  `~ -^(    __;-,((()))
        ~~~~ {_ -_(())
               `\  }
                 { }
""",
    "scroll": r"""
  .-~~-.
 /      \
|        |
|        |
 \      /
  `-..-'
""",
}


def pick_art(entry=None, specific=None):
    if specific:
        return ASCII_ART.get(specific, ASCII_ART["cookie"])
    if entry:
        scheme = entry.scheme
        if scheme in ('q3n', 'orcid') and random.random() > 0.5:
            return ASCII_ART["cat"]
        if scheme == 'isbn' and random.random() > 0.5:
            return ASCII_ART["book"]
        if scheme in ('doi', 'arxiv', 'pubmed') and random.random() > 0.5:
            return ASCII_ART["brain"]
        if scheme in ('yt', 'youtube', 'spotify') and random.random() > 0.5:
            return ASCII_ART["computer"]
    return random.choice(list(ASCII_ART.values()))


def format_fortune(entry, width=60):
    lines = []
    for word in entry.quote.split():
        if not lines:
            lines.append(word)
        elif len(lines[-1]) + len(word) + 1 <= width:
            lines[-1] += ' ' + word
        else:
            lines.append(word)
    if not lines:
        lines = ['']
    lines.append('')
    lines.append(entry.attribution())
    return '\n'.join(lines)


def box_text(text):
    lines = text.split('\n')
    width = min(max((len(l) for l in lines), default=0), 60)
    border = '+' + '-' * (width + 2) + '+'
    out = [border]
    for line in lines:
        out.append('| ' + line.ljust(width) + ' |')
    out.append(border)
    return '\n'.join(out)


def display_fortune(entries, art=None, no_art=False):
    if not entries:
        return "No fortunes found!"
    entry = random.choice(entries)
    formatted = format_fortune(entry)
    result = ''
    if not no_art:
        result += pick_art(entry, art) + '\n'
    result += box_text(formatted)
    return result


def export_fortune(entries):
    out = []
    for e in entries:
        out.append(e.quote)
        out.append('%')
    return '\n'.join(out)
