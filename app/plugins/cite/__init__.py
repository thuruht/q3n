PLUGIN_META = {
    'name': 'cite',
    'title': 'Cite',
    'description': 'Format Q3N entries as MLA, APA, Chicago, or BibTeX citations.',
    'version': '1.0.0',
}


def register(manager):
    from .panel import CitePanelWidget
    manager.register_panel('cite', CitePanelWidget)
    manager.register_standalone('cite', _run_standalone)


def _run_standalone(entries, args):
    import argparse
    p = argparse.ArgumentParser(prog='q3n cite')
    p.add_argument('--style', default='apa',
                   choices=['mla', 'apa', 'chicago', 'bibtex'])
    p.add_argument('--entry', type=int, default=None, metavar='N',
                   help='1-based entry index')
    p.add_argument('--all', action='store_true', dest='all_entries')
    parsed = p.parse_args(args)

    from .formatter import format_citation
    if not entries:
        print('(no entries)')
        return

    if parsed.all_entries:
        for i, e in enumerate(entries, 1):
            print(f'--- Entry {i} ---')
            print(format_citation(e, parsed.style))
            print()
    elif parsed.entry is not None:
        idx = parsed.entry - 1
        if 0 <= idx < len(entries):
            print(format_citation(entries[idx], parsed.style))
        else:
            print(f'(no entry {parsed.entry})')
    else:
        print(format_citation(entries[0], parsed.style))
