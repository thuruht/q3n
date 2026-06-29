#!/usr/bin/env python3
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def _find_app_root():
    for candidate in (Path(__file__).resolve().parent.parent, Path('/usr/lib/q3n')):
        if (candidate / 'app' / 'src' / 'core' / 'plugin_manager.py').exists():
            return candidate
    return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Q3N Manager")
    win = MainWindow()

    app_root = _find_app_root()
    if app_root:
        if str(app_root) not in sys.path:
            sys.path.insert(0, str(app_root))
        try:
            from app.src.core.plugin_manager import PluginManager
            from core.config import get_extra_plugin_dirs
            pm = PluginManager(plugin_dirs=None)
            for extra in get_extra_plugin_dirs():
                if extra not in pm._plugin_dirs:
                    pm._plugin_dirs.append(extra)
            pm.discover()
            win.load_plugins(pm)
        except Exception:
            pass

    try:
        from core.config import get_config, load_last_file
        if get_config()['gui'].getboolean('remember_last_file', False):
            last = load_last_file()
            if last:
                win.open_path(last)
    except Exception:
        pass

    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
