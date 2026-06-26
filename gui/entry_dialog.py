from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QTextEdit, QPushButton, QMessageBox)
from core.q3n import Q3NEntry


class EntryDialog(QDialog):
    def __init__(self, parent=None, entry=None, all_tags=None):
        super().__init__(parent)
        self._entry = entry
        self._all_tags = all_tags or []
        self._setup_ui()
        if entry:
            self.setWindowTitle("Edit Entry")
            self._uri_input.setText(entry.uri)
            self._tag_input.setText(entry.tag or '')
            self._quote_input.setPlainText(entry.quote)
        else:
            self.setWindowTitle("New Entry")

    def _setup_ui(self):
        self.setMinimumSize(550, 400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("URI"))
        self._uri_input = QLineEdit()
        self._uri_input.setPlaceholderText("https://example.com/article")
        layout.addWidget(self._uri_input)

        layout.addWidget(QLabel("Tag"))
        self._tag_input = QLineEdit()
        self._tag_input.setPlaceholderText("e.g. cite/article, quote, note")
        layout.addWidget(self._tag_input)

        layout.addWidget(QLabel("Quote"))
        self._quote_input = QTextEdit()
        self._quote_input.setPlaceholderText("Quoted text content...")
        layout.addWidget(self._quote_input, 1)

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save")
        self._save_btn.clicked.connect(self._accept)
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._reject)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

    def get_entry(self):
        uri = self._uri_input.text().strip()
        tag = self._tag_input.text().strip() or None
        quote = self._quote_input.toPlainText()
        scheme = uri.split('://')[0] if '://' in uri else ''
        path = uri.split('://', 1)[1] if '://' in uri else uri
        return Q3NEntry(uri, scheme, path, quote, tag)

    def accept(self):
        if not self._uri_input.text().strip():
            QMessageBox.warning(self, "Validation", "URI is required.")
            return
        super().accept()
