#!/usr/bin/env python3
"""Q3N Meta-Application Framework — main entry point.

Usage:
    python app/src/main.py                  # Launch Q3N Manager GUI
    python app/src/main.py --fortune        # Launch fortune desktop widget
    python app/src/main.py --designer       # Designer-ready mode (runtime .ui loading)
    python app/src/main.py --list-ui        # List available .ui files
"""

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

_ICON_PATH = _repo_root / 'scripts' / 'AppDir' / 'q3n.png'

from core import __version__


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Q3N')
    app.setApplicationVersion(__version__)
    app.setOrganizationName('Q3N Project')
    if _ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(_ICON_PATH)))

    args = sys.argv[1:]

    if '--fortune' in args:
        _launch_fortune(app)
    elif '--designer' in args:
        _launch_designer_mode(app)
    elif '--list-ui' in args:
        _list_ui_files()
    else:
        _launch_manager(app)

    sys.exit(app.exec())


def _launch_manager(app):
    """Launch the standard Q3N Manager GUI."""
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()


def _launch_fortune(app):
    """Launch the fortune desktop widget."""
    from app.plugins.fortune.widget import FortuneOverlay
    entries = _collect_entries()
    widget = FortuneOverlay(entries=entries)
    widget.setVisible(True)


def _launch_designer_mode(app):
    """Launch designer-ready mode with runtime .ui loading."""
    from app.src.core.ui_loader import UILoader, discover_ui_files

    ui_files = discover_ui_files()
    if not ui_files:
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle('No UI Files')
        msg.setText('No .ui files found in resources/ui/.\n'
                     'Create one with Qt Designer, or run the standard GUI.')
        msg.exec()
        return

    from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QListWidget, QStackedWidget, QLabel

    class DesignerHost(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('Q3N Designer Mode')
            self.resize(900, 600)
            self._loader = UILoader()
            self._setup()

        def _setup(self):
            central = QWidget()
            self.setCentralWidget(central)
            layout = QHBoxLayout(central)

            # Sidebar with available UIs
            self._ui_list = QListWidget()
            self._ui_list.setMaximumWidth(220)
            self._ui_list.currentRowChanged.connect(self._on_ui_selected)
            layout.addWidget(self._ui_list)

            # Preview area
            self._stack = QStackedWidget()
            layout.addWidget(self._stack, 1)

            # Populate list
            ui_files = discover_ui_files()
            for uf in ui_files:
                self._ui_list.addItem(uf.name)
                self._ui_files.append(uf)

            if self._ui_files:
                self._ui_list.setCurrentRow(0)

        def _on_ui_selected(self, row):
            if row < 0 or row >= len(self._ui_files):
                return
            path = self._ui_files[row]
            try:
                # Clear old pages
                while self._stack.count():
                    w = self._stack.widget(0)
                    self._stack.removeWidget(w)
                    w.deleteLater()

                widget = self._loader.load(path, handler=self)
                self._stack.addWidget(widget)
            except Exception as e:
                label = QLabel(f'Error loading {path.name}:\n{e}')
                label.setStyleSheet('color: red; padding: 20px;')
                self._stack.addWidget(label)

    from PySide6.QtWidgets import QHBoxLayout
    host = DesignerHost()
    host.show()


def _list_ui_files():
    """Print available .ui files to stdout."""
    from app.src.core.ui_loader import discover_ui_files
    files = discover_ui_files()
    if files:
        print('Available .ui files:')
        for f in files:
            print(f'  {f}')
    else:
        print('No .ui files found.')


def _collect_entries():
    """Collect entries from common Q3N file locations."""
    entries = []
    from core.q3n import parse_file, list_entries, detect
    # Try command-line arg
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            p = Path(arg)
            if p.exists() and detect(p):
                entries.extend(parse_file(p))
                return entries
    # Scan current directory
    results = list_entries('.')
    for path, file_entries in results:
        entries.extend(file_entries)
    return entries


if __name__ == '__main__':
    main()
