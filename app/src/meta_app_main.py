#!/usr/bin/env python3
"""Q3N Meta-Application Mode — generate standalone app configurations.

Usage:
    python app/src/meta_app_main.py                     # Interactive mode
    python app/src/meta_app_main.py --list-templates    # Show available templates
    python app/src/meta_app_main.py --export my_app     # Export as standalone app
"""

import sys
import shutil
import json
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'


def main():
    args = sys.argv[1:]

    if '--list-templates' in args:
        _list_templates()
    elif '--export' in args:
        idx = args.index('--export')
        if idx + 1 < len(args):
            _export_app(args[idx + 1])
        else:
            print('Usage: meta_app_main.py --export <app_name>')
    else:
        _interactive()


def _list_templates():
    if not TEMPLATES_DIR.exists():
        print('No templates directory found.')
        return
    templates = [d for d in TEMPLATES_DIR.iterdir() if d.is_dir()]
    if templates:
        print('Available templates:')
        for t in templates:
            print(f'  {t.name}')
    else:
        print('No templates yet.')


def _export_app(name):
    """Export a standalone application configuration."""
    target = Path.cwd() / name
    if target.exists():
        print(f'Error: {target} already exists.')
        return

    # Copy template structure
    template = TEMPLATES_DIR / 'default'
    if template.exists():
        shutil.copytree(template, target)
    else:
        target.mkdir(parents=True)

    # Create meta-app manifest
    manifest = {
        'name': name,
        'version': '1.0.0',
        'type': 'q3n-meta-app',
        'q3n_version': '1.0.0',
    }
    (target / 'q3n-app.json').write_text(json.dumps(manifest, indent=2))

    print(f'Exported meta-app to: {target}')
    print(f'Run with: python app/src/main.py --designer {target}/resources/ui/')


def _interactive():
    """Interactive meta-app creation wizard."""
    print('Q3N Meta-Application Creator')
    print('─' * 40)
    name = input('Application name: ').strip()
    if not name:
        print('Cancelled.')
        return
    _export_app(name)


if __name__ == '__main__':
    main()
