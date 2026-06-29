PLUGIN_META = {
    'name': 'fortune',
    'title': 'Fortune',
    'description': 'Random quote overlay and sidebar card.',
    'version': '1.0.0',
}


def register(manager):
    from .panel import FortunePanelWidget
    manager.register_panel('fortune', FortunePanelWidget)
    manager.register_standalone('fortune', _run_standalone)


def _run_standalone(entries, args):
    import sys
    if not entries:
        print('No entries loaded. Usage: q3n run fortune <file>', file=sys.stderr)
        sys.exit(1)
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from .widget import FortuneOverlay
    w = FortuneOverlay(entries=entries)
    w.show()
    sys.exit(app.exec())
