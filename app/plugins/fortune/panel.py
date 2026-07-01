import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QComboBox)


class FortunePanelWidget(QWidget):
    """Compact sidebar card showing a random quote from the open file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        self._tag_combo = QComboBox()
        self._tag_combo.setToolTip("Filter by tag")
        self._tag_combo.addItem("All tags", None)
        self._tag_combo.currentIndexChanged.connect(self._show_random)
        self._scheme_combo = QComboBox()
        self._scheme_combo.setToolTip("Filter by scheme")
        self._scheme_combo.addItem("All schemes", None)
        self._scheme_combo.currentIndexChanged.connect(self._show_random)
        filter_row.addWidget(self._tag_combo, 1)
        filter_row.addWidget(self._scheme_combo, 1)
        layout.addLayout(filter_row)

        self._quote_label = QLabel('No file open.')
        self._quote_label.setObjectName('fortune_quote')
        self._quote_label.setWordWrap(True)
        layout.addWidget(self._quote_label)

        self._attr_label = QLabel('')
        self._attr_label.setObjectName('fortune_attr')
        layout.addWidget(self._attr_label)

        layout.addStretch()

        btn_row = QHBoxLayout()
        next_btn = QPushButton('Next ↻')
        next_btn.clicked.connect(self._show_random)
        popout_btn = QPushButton('Pop out ↗')
        popout_btn.clicked.connect(self._pop_out)
        btn_row.addWidget(next_btn)
        btn_row.addWidget(popout_btn)
        layout.addLayout(btn_row)

    def set_entries(self, entries):
        self._entries = entries
        self._refresh_filters()
        self._show_random()

    def _refresh_filters(self):
        current_tag = self._tag_combo.currentData()
        current_scheme = self._scheme_combo.currentData()

        self._tag_combo.blockSignals(True)
        self._tag_combo.clear()
        self._tag_combo.addItem("All tags", None)
        for tag in sorted({e.tag for e in self._entries if e.tag}):
            self._tag_combo.addItem(tag, tag)
        idx = self._tag_combo.findData(current_tag)
        self._tag_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._tag_combo.blockSignals(False)

        self._scheme_combo.blockSignals(True)
        self._scheme_combo.clear()
        self._scheme_combo.addItem("All schemes", None)
        for scheme in sorted({e.scheme for e in self._entries if e.scheme}):
            self._scheme_combo.addItem(scheme, scheme)
        idx = self._scheme_combo.findData(current_scheme)
        self._scheme_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._scheme_combo.blockSignals(False)

    def _filtered_entries(self):
        tag = self._tag_combo.currentData()
        scheme = self._scheme_combo.currentData()
        result = self._entries
        if tag:
            result = [e for e in result if e.tag == tag]
        if scheme:
            result = [e for e in result if e.scheme == scheme]
        return result

    def _show_random(self):
        pool = self._filtered_entries()
        if not pool:
            self._quote_label.setText('No matching entries.')
            self._attr_label.setText('')
            return
        entry = random.choice(pool)
        quote = entry.quote[:200].strip()
        if len(entry.quote) > 200:
            quote += '…'
        self._quote_label.setText(quote)
        self._attr_label.setText(entry.attribution())

    def _pop_out(self):
        from .widget import FortuneOverlay
        overlay = FortuneOverlay(entries=self._filtered_entries(), parent=None)
        overlay.show()
        self._overlay = overlay
