"""Runtime UI loader with automatic signal-to-handler wiring.

Loads Qt Designer .ui files at runtime (no compilation needed) and
automatically connects signals to handler methods based on naming conventions:

    Widget Signal          → Handler method
    ─────────────────────────────────────────────────
    action_new_quote       → on_action_new_quote_triggered
    refresh_button         → on_refresh_button_clicked
    search_input           → on_search_input_textChanged
    list_widget            → on_list_widget_currentRowChanged
    check_box              → on_check_box_toggled
    combo_box              → on_combo_box_currentIndexChanged

Usage:
    loader = UILoader()
    window = loader.load('path/to/form.ui', parent=self)
"""

from pathlib import Path
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader


class SignalRouter(QObject):
    """Automatically routes Qt signals to handler methods on a target object."""

    def __init__(self, target, widget):
        super().__init__(target)
        self._target = target
        self._wire(widget)

    def _wire(self, obj):
        """Walk widget tree and connect all named signals."""
        meta = obj.metaObject()
        # Connect signals from this object
        for i in range(meta.methodCount()):
            method = meta.method(i)
            if method.methodType() != method.Signal:
                continue
            signal_name = method.name().data().decode()
            handler_name = f'on_{obj.objectName()}_{signal_name}'
            handler = getattr(self._target, handler_name, None)
            if handler:
                signal = getattr(obj, signal_name, None)
                if signal:
                    try:
                        signal.connect(handler)
                    except TypeError:
                        # Parameter mismatch — skip
                        pass
        # Recurse into children
        for child in obj.children():
            if child.metaObject():
                self._wire(child)

    def _find_children(self, widget):
        """Recursive child finder."""
        children = []
        for child in widget.children():
            children.append(child)
            children.extend(self._find_children(child))
        return children


class UILoader:
    """Loads .ui files at runtime and auto-wires signals to a handler object."""

    def __init__(self):
        self._loader = QUiLoader()

    def load(self, ui_path, parent=None, handler=None):
        """Load a .ui file and optionally wire signals to handler.

        Args:
            ui_path: Path to .ui file
            parent: Parent widget (passed to QUiLoader)
            handler: Object whose methods receive auto-wired signals

        Returns:
            The loaded QWidget
        """
        path = Path(ui_path)
        if not path.exists():
            raise FileNotFoundError(f'UI file not found: {path.resolve()}')

        widget = self._loader.load(str(path.resolve()), parent)
        if widget is None:
            raise RuntimeError(f'Failed to load UI: {path}')

        if handler:
            SignalRouter(handler, widget)

        return widget

    def load_from_resource(self, name, parent=None, handler=None):
        """Load a .ui file from the resources/ui/ directory.

        Searches app/resources/ui/ relative to the project root.
        """
        from pathlib import Path
        # Try multiple search paths
        candidates = [
            Path(__file__).resolve().parent.parent.parent / 'resources' / 'ui',
            Path.cwd() / 'resources' / 'ui',
            Path.cwd() / 'app' / 'resources' / 'ui',
        ]
        for base in candidates:
            ui_file = base / f'{name}.ui'
            if ui_file.exists():
                return self.load(ui_file, parent, handler)

        # Try with .ui extension
        for base in candidates:
            ui_file = base / name
            if ui_file.exists():
                return self.load(ui_file, parent, handler)

        raise FileNotFoundError(
            f'UI resource "{name}" not found in any search path.\n'
            f'Searched: {[str(c) for c in candidates]}')


def discover_ui_files():
    """Return list of available .ui files in all resource directories."""
    from pathlib import Path
    candidates = [
        Path(__file__).resolve().parent.parent.parent / 'resources' / 'ui',
        Path.cwd() / 'resources' / 'ui',
        Path.cwd() / 'app' / 'resources' / 'ui',
    ]
    ui_files = []
    for base in candidates:
        if base.exists():
            ui_files.extend(sorted(base.glob('*.ui')))
    return ui_files
