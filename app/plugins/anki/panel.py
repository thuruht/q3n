from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                               QPushButton, QTextEdit, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import Qt


class AnkiPanelWidget(QWidget):
    """Sidebar tab for exporting Q3N entries to Anki-compatible CSV."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self._info = QLabel('No entries loaded.')
        self._info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._info)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setPlaceholderText('CSV preview will appear here.')
        layout.addWidget(self._preview, 1)

        export_btn = QPushButton('Export CSV...')
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn)

    def set_entries(self, entries):
        self._entries = entries
        if entries:
            self._info.setText(f'{len(entries)} entries ready for export')
            from .export import export_anki_csv
            text = export_anki_csv(entries)
            lines = text.splitlines()
            preview = '\n'.join(lines[:6])
            if len(lines) > 6:
                preview += f'\n... ({len(lines) - 6} more rows)'
            self._preview.setPlainText(preview)
        else:
            self._info.setText('No entries loaded.')
            self._preview.clear()

    def _export(self):
        if not self._entries:
            QMessageBox.information(self, 'Export', 'No entries to export.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export Anki CSV', '', 'CSV Files (*.csv)')
        if not path:
            return
        from .export import export_anki_csv
        text = export_anki_csv(self._entries)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        QMessageBox.information(
            self, 'Export',
            f'Exported {len(self._entries)} entries to {path}')
