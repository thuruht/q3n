import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton)


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
        self._show_random()

    def _show_random(self):
        if not self._entries:
            self._quote_label.setText('No entries.')
            self._attr_label.setText('')
            return
        entry = random.choice(self._entries)
        quote = entry.quote[:200].strip()
        if len(entry.quote) > 200:
            quote += '…'
        self._quote_label.setText(quote)
        self._attr_label.setText(entry.attribution())

    def _pop_out(self):
        from app.plugins.fortune.widget import FortuneOverlay
        overlay = FortuneOverlay(entries=self._entries, parent=None)
        overlay.show()
        self._overlay = overlay
