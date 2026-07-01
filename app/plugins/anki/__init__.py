PLUGIN_META = {
    'name': 'anki',
    'title': 'Anki',
    'description': 'Export Q3N entries as Anki-compatible CSV for flashcard import.',
    'version': '1.0.0',
}


def register(manager):
    manager.register_standalone('anki', _run_standalone)


def _run_standalone(entries, args):
    import argparse
    p = argparse.ArgumentParser(prog='q3n anki')
    p.add_argument('--output', '-o', default=None, help='Output CSV file')
    parsed = p.parse_args(args)

    from .export import export_anki_csv
    text = export_anki_csv(entries)
    if parsed.output:
        with open(parsed.output, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Wrote {len(entries)} entries to {parsed.output}')
    else:
        print(text)
