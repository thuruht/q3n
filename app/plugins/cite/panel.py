from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QComboBox, QTextEdit, QPushButton,
                               QListWidget, QLabel, QApplication,
                               QSplitter)
from PySide6.QtCore import Qt


class CitePanelWidget(QWidget):
    """Sidebar tab for formatting Q3N entries as citations."""

    STYLES = [('MLA 9', 'mla'), ('APA 7', 'apa'),
              ('Chicago 17', 'chicago'), ('BibTeX', 'bibtex')]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._setup_ui()
        self._apply_default_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel('Style:'))
        self._style_combo = QComboBox()
        for label, _ in self.STYLES:
            self._style_combo.addItem(label)
        self._style_combo.currentIndexChanged.connect(self._refresh)
        top_row.addWidget(self._style_combo)
        top_row.addStretch()
        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Vertical)

        self._entry_list = QListWidget()
        self._entry_list.currentRowChanged.connect(self._refresh)
        splitter.addWidget(self._entry_list)

        self._citation_box = QTextEdit()
        self._citation_box.setObjectName('citation_box')
        self._citation_box.setReadOnly(True)
        splitter.addWidget(self._citation_box)

        layout.addWidget(splitter, 1)

        copy_btn = QPushButton('Copy to clipboard')
        copy_btn.clicked.connect(self._copy)
        layout.addWidget(copy_btn)

    def set_entries(self, entries):
        self._entries = entries
        self._entry_list.clear()
        for e in entries:
            preview = e.quote[:50].replace('\n', ' ')
            self._entry_list.addItem(f'[{e.scheme}] {preview}')
        if entries:
            self._entry_list.setCurrentRow(0)
        self._refresh()

    def _apply_default_style(self):
        try:
            from core.config import get_config
            default = get_config()['plugins'].get('default_citation_style', 'apa').lower()
            keys = [key for _, key in self.STYLES]
            if default in keys:
                self._style_combo.setCurrentIndex(keys.index(default))
        except Exception:
            pass

    def _current_style(self):
        idx = self._style_combo.currentIndex()
        return self.STYLES[idx][1] if 0 <= idx < len(self.STYLES) else 'apa'

    def _refresh(self):
        row = self._entry_list.currentRow()
        if row < 0 or row >= len(self._entries):
            self._citation_box.setPlainText('')
            return
        from app.plugins.cite.formatter import format_citation
        try:
            result = format_citation(self._entries[row], self._current_style())
        except Exception as e:
            result = f'(error: {e})'
        self._citation_box.setPlainText(result)

    def _copy(self):
        QApplication.clipboard().setText(self._citation_box.toPlainText())
