"""User configuration for Q3N.

Config file location: $XDG_CONFIG_HOME/q3n/q3n.conf (default: ~/.config/q3n/q3n.conf)

Example q3n.conf:
    [core]
    # Max file size (bytes) for content-based detection (files without a recognised extension)
    scan_max_bytes = 10485760

    # Default export format when -f is not specified
    default_export_format = q3n

    [gui]
    # Path to a custom Qt stylesheet (.qss). Leave empty to use the built-in theme.
    # style_file = /home/you/.config/q3n/style.qss

    [plugins]
    # Extra plugin directories to search (comma-separated paths)
    # extra_dirs = /home/you/.local/share/q3n/plugins, /opt/q3n-plugins

    # Default citation style: mla, apa, chicago, bibtex
    default_citation_style = apa
"""

import configparser
import os
from pathlib import Path

_CONFIG = None


def config_path():
    xdg = os.environ.get('XDG_CONFIG_HOME', '')
    base = Path(xdg) if xdg else Path.home() / '.config'
    return base / 'q3n' / 'q3n.conf'


def get_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load()
    return _CONFIG


def _load():
    cfg = configparser.ConfigParser()
    cfg['core'] = {
        'scan_max_bytes': '10485760',
        'default_export_format': 'q3n',
    }
    cfg['gui'] = {
        'style_file': '',
        'remember_last_file': 'false',
    }
    cfg['plugins'] = {
        'extra_dirs': '',
        'default_citation_style': 'apa',
    }
    path = config_path()
    if path.exists():
        cfg.read(path)
    return cfg


def state_path():
    xdg = os.environ.get('XDG_STATE_HOME', '')
    base = Path(xdg) if xdg else Path.home() / '.local' / 'state'
    return base / 'q3n' / 'last_file'


def save_last_file(path):
    sp = state_path()
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(str(path))


def load_last_file():
    sp = state_path()
    if sp.exists():
        p = Path(sp.read_text().strip())
        return p if p.exists() else None
    return None


def get_extra_plugin_dirs():
    raw = get_config()['plugins'].get('extra_dirs', '').strip()
    if not raw:
        return []
    return [Path(p.strip()) for p in raw.split(',') if p.strip()]


def get_style_file():
    path_str = get_config()['gui'].get('style_file', '').strip()
    if not path_str:
        default = config_path().parent / 'style.qss'
        if default.exists():
            return default
        return None
    p = Path(path_str)
    return p if p.exists() else None
