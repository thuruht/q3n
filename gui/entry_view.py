from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QTextEdit, QPushButton, QFrame,
                               QMessageBox)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from core.q3n import Q3NEntry, validate_uri, parse_scheme

SCHEME_ICONS = {
    'https': '🌐', 'http': '🌐', 'file': '📄',
    'isbn': '📚', 'doi': '📖', 'arxiv': '📋',
    'pubmed': '🔬', 'orcid': '👤', 'spotify': '🎵',
    'q3n': '👤', 'yt': '🎬', 'youtube': '🎬',
    'osm': '🗺️', 'geo': '🗺️', 'overpass': '🗺️',
    'wikipedia': '📖',
    'github': '🐙',
}

CATEGORY_COLORS = {
    'web': '#4a90d9',
    'file': '#27ae60',
    'book': '#8e44ad',
    'academic': '#2c3e50',
    'person': '#e67e22',
    'media': '#e74c3c',
    'map': '#16a085',
}


class EntryDetailView(QWidget):
    entry_changed = Signal(int, Q3NEntry)

    def __init__(self):
        super().__init__()
        self._row = -1
        self._entry = None
        self._dirty = False
        self._setup_ui()
        self.set_enabled(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Entry Detail")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding-bottom: 4px;")
        layout.addWidget(title)

        form = QVBoxLayout()
        form.setSpacing(6)

        self._uri_label = QLabel("URI")
        uri_row = QHBoxLayout()
        self._uri_input = QLineEdit()
        self._uri_input.setPlaceholderText("https://example.com/article")
        self._uri_input.textChanged.connect(self._mark_dirty)
        self._uri_input.textChanged.connect(self._update_validation)
        self._open_btn = QPushButton("Open ↗")
        self._open_btn.setFixedWidth(72)
        self._open_btn.setToolTip("Open source URL in browser")
        self._open_btn.clicked.connect(self._open_url)
        uri_row.addWidget(self._uri_input)
        uri_row.addWidget(self._open_btn)
        self._validation_label = QLabel("")
        self._validation_label.setStyleSheet("font-size: 11px;")
        form.addWidget(self._uri_label)
        form.addLayout(uri_row)
        form.addWidget(self._validation_label)

        self._attribution_label = QLabel("Attribution")
        self._attribution_value = QLabel("")
        self._attribution_value.setStyleSheet("color: #666; font-style: italic; padding: 2px 0;")
        self._attribution_value.setWordWrap(True)
        form.addWidget(self._attribution_label)
        form.addWidget(self._attribution_value)

        meta_row = QHBoxLayout()
        self._category_label = QLabel("")
        self._category_label.setStyleSheet(
            "padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;")
        self._metadata_value = QLabel("")
        self._metadata_value.setStyleSheet("color: #888;")
        meta_row.addWidget(self._category_label)
        meta_row.addWidget(self._metadata_value, 1)
        form.addLayout(meta_row)

        tag_row = QHBoxLayout()
        self._tag_label = QLabel("Tag")
        self._tag_input = QLineEdit()
        self._tag_input.setPlaceholderText("e.g. cite/article, quote, note")
        self._tag_input.textChanged.connect(self._mark_dirty)
        self._scheme_label = QLabel("Scheme:")
        self._scheme_value = QLabel("")
        self._scheme_value.setStyleSheet("color: #888;")
        tag_row.addWidget(self._tag_label)
        tag_row.addWidget(self._tag_input, 1)
        tag_row.addWidget(self._scheme_label)
        tag_row.addWidget(self._scheme_value)
        form.addLayout(tag_row)

        self._quote_label = QLabel("Quote")
        self._quote_input = QTextEdit()
        self._quote_input.setPlaceholderText("Quoted text content...")
        self._quote_input.setMinimumHeight(160)
        self._quote_input.textChanged.connect(self._mark_dirty)
        form.addWidget(self._quote_label)
        form.addWidget(self._quote_input)

        self._source_label = QLabel("Q3N Source")
        self._source_label.setStyleSheet("font-size: 11px; color: #888; margin-top: 6px;")
        self._source_view = QTextEdit()
        self._source_view.setReadOnly(True)
        self._source_view.setMaximumHeight(90)
        self._source_view.setStyleSheet(
            "font-family: monospace; font-size: 11px; background: #f8f8f8; color: #555;")
        form.addWidget(self._source_label)
        form.addWidget(self._source_view)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save")
        self._save_btn.clicked.connect(self._save)
        self._cancel_btn = QPushButton("Revert")
        self._cancel_btn.clicked.connect(self._revert)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)
        layout.addStretch()

    def set_enabled(self, enabled):
        self._uri_input.setEnabled(enabled)
        self._open_btn.setEnabled(enabled)
        self._tag_input.setEnabled(enabled)
        self._quote_input.setEnabled(enabled)
        self._save_btn.setEnabled(enabled)
        self._cancel_btn.setEnabled(enabled)

    def _mark_dirty(self):
        self._dirty = True

    def _update_validation(self):
        uri = self._uri_input.text().strip()
        if not uri:
            self._validation_label.setText('')
            return
        errors = validate_uri(uri)
        if errors:
            self._validation_label.setText(f'⚠ {errors[0]}')
            self._validation_label.setStyleSheet('color: #e74c3c; font-size: 11px;')
        else:
            self._validation_label.setText('✓ valid')
            self._validation_label.setStyleSheet('color: #27ae60; font-size: 11px;')

    def show_entry(self, row, entry):
        self._row = row
        self._entry = entry
        self._uri_input.blockSignals(True)
        self._tag_input.blockSignals(True)
        self._quote_input.blockSignals(True)
        self._uri_input.setText(entry.uri)
        self._tag_input.setText(entry.tag or '')
        self._quote_input.setPlainText(entry.quote)
        self._uri_input.blockSignals(False)
        self._tag_input.blockSignals(False)
        self._quote_input.blockSignals(False)
        self._dirty = False
        self._scheme_value.setText(entry.scheme)
        self._update_validation()
        icon = SCHEME_ICONS.get(entry.scheme, '🔗')
        self._attribution_value.setText(f'{icon} {entry.attribution()}' if entry.attribution() else icon)
        derived = entry.as_dict()
        category = derived.get('category', '')
        if category:
            color = CATEGORY_COLORS.get(category, '#888')
            self._category_label.setText(f' {category.upper()} ')
            self._category_label.setStyleSheet(
                f"background: {color}; color: white; padding: 2px 8px; "
                f"border-radius: 3px; font-size: 11px; font-weight: bold;")
            self._category_label.setVisible(True)
        else:
            self._category_label.setVisible(False)
        meta = derived.get('meta', {})
        meta_parts = []
        if 'domain' in meta:
            meta_parts.append(f'domain: {meta["domain"]}')
        if 'author' in meta:
            meta_parts.append(f'by {meta["author"]}')
        if 'title' in meta:
            meta_parts.append(f'"{meta["title"]}"')
        if 'video_id' in meta:
            meta_parts.append(f'video: {meta["video_id"]}')
        if 'isbn' in meta:
            meta_parts.append(f'ISBN: {meta["isbn"]}')
        if 'doi' in meta:
            meta_parts.append(f'DOI: {meta["doi"]}')
        if 'arxiv_id' in meta:
            meta_parts.append(f'arXiv: {meta["arxiv_id"]}')
        if 'pmid' in meta:
            meta_parts.append(f'PMID: {meta["pmid"]}')
        if 'orcid' in meta:
            meta_parts.append(f'ORCID: {meta["orcid"]}')
        if 'kind' in meta and entry.scheme == 'spotify':
            meta_parts.append(f'{meta["kind"]}: {meta.get("id", "")}')
        if 'name' in meta:
            meta_parts.append(meta['name'])
        if 'email' in meta:
            meta_parts.append(meta['email'])
        if 'path' in meta and entry.scheme == 'file':
            meta_parts.append(f'path: {meta["path"]}')
        if 'line' in meta:
            meta_parts.append(f'line {meta["line"]}')
        if 'lat' in meta and 'lon' in meta:
            zoom = f'  z{meta["zoom"]}' if 'zoom' in meta else ''
            meta_parts.append(f'{meta["lat"]}, {meta["lon"]}{zoom}')
        if 'type' in meta and 'id' in meta and entry.scheme == 'osm':
            meta_parts.append(f'{meta["type"]}/{meta["id"]}')
        if 'query' in meta and entry.scheme == 'overpass':
            q = meta['query']
            meta_parts.append(f'query: {q[:50]}{"…" if len(q) > 50 else ""}')
        self._metadata_value.setText(' · '.join(meta_parts) if meta_parts else '')
        tag_part = f' /// {entry.tag}:' if entry.tag else ''
        self._source_view.setPlainText(
            f'/// {entry.uri}{tag_part}\n{entry.quote}\n\\\\\\')
        self.set_enabled(True)

    def clear(self):
        self._row = -1
        self._entry = None
        self._dirty = False
        self._uri_input.clear()
        self._tag_input.clear()
        self._quote_input.clear()
        self._scheme_value.clear()
        self._attribution_value.clear()
        self._category_label.setVisible(False)
        self._metadata_value.clear()
        self._validation_label.setText('')
        self._source_view.clear()
        self.set_enabled(False)

    def _open_url(self):
        if not self._entry:
            return
        meta = self._entry.as_dict().get('meta', {})
        url = (meta.get('browse_url') or meta.get('map_url')
               or (self._entry.uri if self._entry.uri.startswith(('https://', 'http://')) else None))
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _save(self):
        if not self._dirty or self._row < 0:
            return
        uri = self._uri_input.text().strip()
        if not uri:
            QMessageBox.warning(self, "Validation", "URI is required.")
            return
        tag = self._tag_input.text().strip() or None
        quote = self._quote_input.toPlainText()
        scheme, path = parse_scheme(uri)
        entry = Q3NEntry(uri, scheme, path, quote, tag)
        self._entry = entry
        self._dirty = False
        tag_part = f' /// {tag}:' if tag else ''
        self._source_view.setPlainText(f'/// {uri}{tag_part}\n{quote}\n\\\\\\')
        self.entry_changed.emit(self._row, entry)

    def _revert(self):
        if self._entry:
            self._uri_input.setText(self._entry.uri)
            self._tag_input.setText(self._entry.tag or '')
            self._quote_input.setPlainText(self._entry.quote)
            self._dirty = False
