import re
from collections import Counter
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QSplitter, QListView, QWidget,
                               QVBoxLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QLabel, QComboBox, QMenuBar,
                               QMenu, QFileDialog, QMessageBox, QStatusBar,
                               QStyledItemDelegate, QStyle, QApplication,
                               QToolBar, QCheckBox, QDialog, QTextEdit,
                               QDockWidget, QTabWidget, QFormLayout,
                               QTextBrowser, QTableWidget, QTableWidgetItem,
                               QHeaderView, QDialogButtonBox)
from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtGui import QAction, QPalette, QFont, QIcon

_ICON_PATH = Path(__file__).resolve().parent.parent / 'scripts' / 'AppDir' / 'q3n.png'

QSS = """
QMainWindow {
    background-color: #fafafa;
}
QListView {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 2px;
    font-size: 13px;
}
QListView::item:selected {
    background-color: #cce5ff;
    color: #003366;
}
QListView::item:hover {
    background-color: #f0f8ff;
}
QLineEdit {
    border: 1px solid #ccc;
    border-radius: 3px;
    padding: 4px 6px;
    font-size: 13px;
    background: white;
}
QLineEdit:focus {
    border-color: #4a90d9;
}
QPushButton {
    border: 1px solid #bbb;
    border-radius: 3px;
    padding: 5px 14px;
    font-size: 13px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #fcfcfc, stop:1 #eaeaea);
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffffff, stop:1 #f0f0f0);
    border-color: #999;
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ddd, stop:1 #ccc);
}
QComboBox {
    border: 1px solid #ccc;
    border-radius: 3px;
    padding: 4px 6px;
    font-size: 13px;
    background: white;
    min-width: 120px;
}
QStatusBar {
    border-top: 1px solid #ddd;
    font-size: 12px;
    color: #666;
}
QToolBar {
    border-bottom: 1px solid #ddd;
    padding: 2px;
    background: #f5f5f5;
    spacing: 4px;
}
QMenuBar {
    background: #f5f5f5;
    border-bottom: 1px solid #ddd;
    font-size: 13px;
}
QMenuBar::item:selected {
    background: #cce5ff;
}
QMenu {
    background: white;
    border: 1px solid #ccc;
    padding: 4px;
}
QMenu::item {
    padding: 4px 24px;
}
QMenu::item:selected {
    background: #cce5ff;
}
QTextEdit {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px;
    background: white;
    font-size: 13px;
}
QSplitter::handle {
    background: #e0e0e0;
    width: 2px;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
/* Plugin panel widgets — overridable via style.qss */
QLabel#fortune_quote {
    font-size: 13px;
    color: #222;
}
QLabel#fortune_attr {
    font-size: 11px;
    color: #888;
}
QTextEdit#citation_box {
    font-family: monospace;
    font-size: 12px;
}
"""


_DEFAULT_THEME = Path(__file__).resolve().parent / 'q3n_scriptorium.qss'


def _load_stylesheet():
    from core.config import get_style_file
    style_file = get_style_file()
    if style_file:
        try:
            return style_file.read_text()
        except Exception:
            pass
    if _DEFAULT_THEME.exists():
        try:
            return _DEFAULT_THEME.read_text()
        except Exception:
            pass
    return QSS


from core import __version__
from core.q3n import (Q3NEntry, parse_file, serialize_file, export_file,
                      export_json, export_markdown, export_plaintext,
                      generate_index, import_json)
from gui.entry_model import EntryListModel
from gui.entry_view import EntryDetailView
from gui.entry_wizard import EntryWizard


SCHEME_DISPLAY_ICONS = {
    'https': '🌐', 'http': '🌐', 'file': '📄',
    'isbn': '📚', 'doi': '📖', 'arxiv': '📋',
    'pubmed': '🔬', 'orcid': '👤', 'spotify': '🎵',
    'q3n': '👤', 'yt': '🎬', 'youtube': '🎬',
    'wikipedia': '📖',
    'github': '🐙',
}


class EntryDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        e = index.data(Qt.UserRole)
        if not e:
            return
        painter.save()
        icon = SCHEME_DISPLAY_ICONS.get(e.scheme, '🔗')
        preview = e.quote[:60].replace('\n', ' ')
        tag_str = f' [{e.tag}]' if e.tag else ''
        attr = e.attribution()
        text = f'{icon} {preview}{tag_str}'
        palette = option.palette
        text_rect = option.rect.adjusted(4, 4, -4, 0)
        title_rect = text_rect.adjusted(0, 0, 0, -14)
        subtitle_rect = text_rect.adjusted(20, 0, 0, 0)
        if option.state & QStyle.State_Selected:
            title_color = palette.color(QPalette.HighlightedText)
            subtitle_color = palette.color(QPalette.HighlightedText)
        else:
            title_color = palette.color(QPalette.WindowText)
            subtitle_color = palette.color(QPalette.PlaceholderText)
        title_font = painter.font()
        title_font.setBold(False)
        painter.setFont(title_font)
        painter.setPen(title_color)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, text)
        subtitle_font = painter.font()
        subtitle_font.setPointSize(max(subtitle_font.pointSize() - 2, 8))
        painter.setFont(subtitle_font)
        painter.setPen(subtitle_color)
        painter.drawText(subtitle_rect, Qt.AlignLeft | Qt.AlignBottom, attr)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 50)


class TagFilterCombo(QComboBox):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.addItem("All tags", None)
        self.currentIndexChanged.connect(self.changed)

    def set_tags(self, entries):
        current = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem("All tags", None)
        tags = sorted({e.tag for e in entries if e.tag})
        for t in tags:
            self.addItem(t, t)
        idx = self.findData(current)
        if idx >= 0:
            self.setCurrentIndex(idx)
        self.blockSignals(False)

    def selected_tag(self):
        return self.currentData()


class PreviewDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(content)
        text.setStyleSheet("font-family: monospace;")
        layout.addWidget(text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


TUTORIAL_PAGES = [
    ("What is Q3N?",
     "<h3>What is Q3N?</h3>"
     "<p>Q3N (Quote Triple-Slash Notation) is a plain-text format for storing quotations "
     "with their source URIs. Each entry wraps quoted content between <code>///</code> and "
     "<code>\\\\\\</code> delimiters, with the source URI on the opening line.</p>"
     "<p>Think of it as a lightweight, human-readable citation database that lives in "
     "normal text files — no database, no proprietary format, just text.</p>"),
    ("The Format",
     "<h3>Q3N in 30 seconds</h3>"
     "<pre style='background:#f5f5f5;padding:8px;border-radius:4px;'>"
     "/// https://example.com/article /// cite/article:\n"
     "The quoted text goes here.\n"
     "Multiple paragraphs are fine.\n"
     "\\\\\\</pre>"
     "<ul>"
     "<li>Open with <code>/// &lt;source_uri&gt; [/// &lt;tag&gt;:]</code></li>"
     "<li>Content in the middle — any text, multiple lines</li>"
     "<li>Close with <code>\\\\\\</code> on its own line</li>"
     "<li>Optional <code>#!q3n-format</code> header identifies the file</li>"
     "<li>Tags use slash hierarchy: <code>cite/article</code>, <code>note/idea</code></li>"
     "</ul>"),
    ("Getting Started",
     "<h3>Getting Started</h3>"
     "<p>In Q3N Manager:</p>"
     "<ol>"
     "<li>Click <b>File → New</b> to create a blank collection, then <b>Save As</b> to name it.</li>"
     "<li>Click <b>+ New</b> (or <b>+ Entry</b> in the toolbar) to open the entry wizard.</li>"
     "<li>Pick a source type (web, book, DOI, etc.), enter the URI and optional tag, "
     "paste the quote, and click Finish.</li>"
     "<li>Click <b>Save</b> (Ctrl+S) to write to disk.</li>"
     "</ol>"
     "<p>Or open an existing file with <b>File → Open</b> (Ctrl+O).</p>"),
    ("Viewing &amp; Editing",
     "<h3>Viewing &amp; Editing</h3>"
     "<p>Click any entry in the left list to see its full detail in the right panel:</p>"
     "<ul>"
     "<li><b>URI</b> — edit it inline; the ✓/⚠ badge validates it in real time</li>"
     "<li><b>Open ↗</b> — opens the source URL in your browser</li>"
     "<li><b>Tag</b> — edit the slash-hierarchy tag</li>"
     "<li><b>Quote</b> — edit the quoted text</li>"
     "<li><b>Q3N Source</b> — read-only view of the raw format</li>"
     "<li>Click <b>Save</b> to commit edits, or <b>Revert</b> to discard</li>"
     "</ul>"),
    ("Search &amp; Filter",
     "<h3>Search &amp; Filter</h3>"
     "<p>Use the search bar at the top-left to filter entries in real time:</p>"
     "<ul>"
     "<li>Searches both the <b>quote text</b> and the <b>URI</b></li>"
     "<li>Tick the <b>Regex</b> checkbox to use regular expressions "
     "(e.g. <code>Stonewall|Liberation</code>)</li>"
     "<li>Use the <b>tag dropdown</b> to filter by a specific tag</li>"
     "<li>Press <b>Ctrl+F</b> to jump to the search bar</li>"
     "</ul>"),
    ("Exporting",
     "<h3>Exporting</h3>"
     "<p>Use the <b>Export</b> menu to save your collection in different formats:</p>"
     "<ul>"
     "<li><b>Q3N</b> — canonical round-trip format</li>"
     "<li><b>JSON</b> — structured data with all metadata</li>"
     "<li><b>Markdown</b> — blockquote format for wikis and notes</li>"
     "<li><b>HTML</b> — self-contained webpage</li>"
     "<li><b>Plain Text</b> — stripped of all markup</li>"
     "<li><b>Fortune</b> — Unix fortune-cookie format</li>"
     "<li><b>Anki CSV</b> — import directly into Anki for flashcards</li>"
     "</ul>"
     "<p>Use <b>Tools → Preview as JSON/Markdown</b> to see output before saving.</p>"),
    ("URI Schemes",
     "<h3>URI Schemes</h3>"
     "<p>Q3N recognises many source types and extracts metadata automatically:</p>"
     "<table style='border-collapse:collapse;'>"
     "<tr><td style='padding:2px 8px;'>🌐 <code>https://</code></td><td>Web pages</td></tr>"
     "<tr><td style='padding:2px 8px;'>📄 <code>file://</code></td><td>Local files (append <code>#line=N</code>)</td></tr>"
     "<tr><td style='padding:2px 8px;'>📚 <code>isbn://</code></td><td>Books (ISBN;Title;Author;Year)</td></tr>"
     "<tr><td style='padding:2px 8px;'>📖 <code>doi://</code></td><td>Academic papers</td></tr>"
     "<tr><td style='padding:2px 8px;'>📋 <code>arxiv://</code></td><td>arXiv preprints</td></tr>"
     "<tr><td style='padding:2px 8px;'>🎬 <code>yt://</code></td><td>YouTube videos</td></tr>"
     "<tr><td style='padding:2px 8px;'>📖 <code>wikipedia://</code></td><td>Wikipedia articles</td></tr>"
     "<tr><td style='padding:2px 8px;'>🐙 <code>github://</code></td><td>GitHub repos, issues, PRs</td></tr>"
     "<tr><td style='padding:2px 8px;'>🗺️ <code>osm://</code></td><td>OpenStreetMap features</td></tr>"
     "<tr><td style='padding:2px 8px;'>🗺️ <code>geo:</code></td><td>Geographic coordinates</td></tr>"
     "</table>"),
    ("Tips &amp; Next Steps",
     "<h3>Tips &amp; Next Steps</h3>"
     "<ul>"
     "<li>Open a whole <b>directory</b> with <b>File → Open Directory</b> to browse across "
     "multiple files at once</li>"
     "<li>Use <b>Import</b> to merge Q3N, JSON, or plain-text files into the current "
     "collection</li>"
     "<li>The <b>Plugins</b> dock (right side) shows the Fortune and Cite panels — "
     "use the tag/scheme filters in Fortune to explore your collection</li>"
     "<li>Check <b>Tools → Statistics</b> for word counts, scheme breakdown, and tag "
     "frequency</li>"
     "<li>Configure defaults (citation style, theme, etc.) in "
     "<b>Edit → Preferences</b></li>"
     "<li>The <code>q3n</code> CLI provides the same features in the terminal — "
     "run <code>q3n --help</code> or <code>man q3n</code></li>"
     "</ul>"),
]


class StatsDialog(QDialog):
    def __init__(self, entries, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Collection Statistics")
        self.setMinimumSize(500, 450)
        layout = QVBoxLayout(self)

        if not entries:
            layout.addWidget(QLabel("No entries loaded."))
        else:
            n = len(entries)
            words = sum(len(e.quote.split()) for e in entries)
            chars = sum(len(e.quote) for e in entries)
            schemes = Counter(e.scheme for e in entries)
            tags = Counter(e.tag for e in entries if e.tag)
            from core.q3n import URI_PARSERS
            domains = Counter()
            for e in entries:
                if e.scheme in ('https', 'http'):
                    try:
                        meta = URI_PARSERS[e.scheme](e.uri)
                        if 'domain' in meta:
                            domains[meta['domain']] += 1
                    except (ValueError, KeyError, AttributeError):
                        pass

            def bar(count, total, width=20):
                filled = int(width * count / total) if total else 0
                return '█' * filled + '░' * (width - filled)

            lines = [
                f"{'Entries:':<16} {n}",
                f"{'Words:':<16} {words:,}",
                f"{'Characters:':<16} {chars:,}",
                f"{'Avg words/entry:':<16} {words // n if n else 0}",
                "",
                "── Schemes ─────────────────────────",
            ]
            for scheme, count in schemes.most_common():
                lines.append(f"  {scheme:<14} {count:>4}  {bar(count, n)}")
            if tags:
                lines += ["", "── Tags (top 15) ────────────────────"]
                for tag, count in tags.most_common(15):
                    label = (tag[:18] + '…') if len(tag) > 19 else tag
                    lines.append(f"  {label:<20} {count:>4}  {bar(count, n)}")
            if domains:
                lines += ["", "── Domains (top 10) ─────────────────"]
                for domain, count in domains.most_common(10):
                    label = (domain[:23] + '…') if len(domain) > 24 else domain
                    lines.append(f"  {label:<25} {count:>4}  {bar(count, n)}")

            text = QTextEdit()
            text.setReadOnly(True)
            text.setPlainText('\n'.join(lines))
            text.setStyleSheet("font-family: monospace; font-size: 12px;")
            layout.addWidget(text)

        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(480)
        from core.config import get_config, config_path
        self._cfg_path = config_path()
        cfg = get_config()
        layout = QVBoxLayout(self)

        def section(title):
            lbl = QLabel(f"<b>{title}</b>")
            lbl.setStyleSheet("margin-top: 8px;")
            layout.addWidget(lbl)

        def row(form, label, widget):
            form.addRow(QLabel(label), widget)
            return widget

        section("[core]")
        form1 = QFormLayout()
        self._scan_max = QLineEdit(cfg['core'].get('scan_max_bytes', '10485760'))
        self._default_fmt = QLineEdit(cfg['core'].get('default_export_format', 'q3n'))
        row(form1, "scan_max_bytes", self._scan_max)
        row(form1, "default_export_format", self._default_fmt)
        layout.addLayout(form1)

        section("[gui]")
        form2 = QFormLayout()
        self._style_file = QLineEdit(cfg['gui'].get('style_file', ''))
        self._style_file.setPlaceholderText("Leave empty for built-in Scriptorium theme")
        self._remember = QCheckBox()
        self._remember.setChecked(cfg['gui'].getboolean('remember_last_file', False))
        row(form2, "style_file", self._style_file)
        row(form2, "remember_last_file", self._remember)
        layout.addLayout(form2)

        section("[plugins]")
        form3 = QFormLayout()
        self._extra_dirs = QLineEdit(cfg['plugins'].get('extra_dirs', ''))
        self._extra_dirs.setPlaceholderText("Comma-separated paths")
        self._cite_style = QComboBox()
        for s in ['apa', 'mla', 'chicago', 'bibtex']:
            self._cite_style.addItem(s)
        current = cfg['plugins'].get('default_citation_style', 'apa')
        idx = self._cite_style.findText(current)
        if idx >= 0:
            self._cite_style.setCurrentIndex(idx)
        row(form3, "extra_dirs", self._extra_dirs)
        row(form3, "default_citation_style", self._cite_style)
        layout.addLayout(form3)

        note = QLabel(f"<i>Config file: {self._cfg_path}</i>")
        note.setStyleSheet("font-size: 11px; color: #888; margin-top: 8px;")
        layout.addWidget(note)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _save(self):
        import configparser
        cfg = configparser.ConfigParser(interpolation=None)
        cfg['core'] = {
            'scan_max_bytes': self._scan_max.text().strip() or '10485760',
            'default_export_format': self._default_fmt.text().strip() or 'q3n',
        }
        cfg['gui'] = {
            'style_file': self._style_file.text().strip(),
            'remember_last_file': 'true' if self._remember.isChecked() else 'false',
        }
        cfg['plugins'] = {
            'extra_dirs': self._extra_dirs.text().strip(),
            'default_citation_style': self._cite_style.currentText(),
        }
        try:
            self._cfg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cfg_path, 'w') as f:
                cfg.write(f)
            import core.config as _cc
            _cc._CONFIG = None  # force reload on next access
            self.accept()
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not save settings:\n{e}")


class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Q3N Tutorial")
        self.setMinimumSize(560, 420)
        self._page = 0
        layout = QVBoxLayout(self)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        layout.addWidget(self._browser)

        nav = QHBoxLayout()
        self._prev_btn = QPushButton("← Previous")
        self._prev_btn.clicked.connect(self._prev)
        self._next_btn = QPushButton("Next →")
        self._next_btn.clicked.connect(self._next)
        self._page_label = QLabel()
        self._page_label.setAlignment(Qt.AlignCenter)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._page_label, 1)
        nav.addWidget(self._next_btn)
        nav.addWidget(close_btn)
        layout.addLayout(nav)
        self._show_page()

    def _show_page(self):
        title, html = TUTORIAL_PAGES[self._page]
        self._browser.setHtml(
            f"<style>body{{font-family:sans-serif;font-size:13px;}} "
            f"code{{background:#f0f0f0;padding:1px 4px;border-radius:3px;}} "
            f"pre{{background:#f5f5f5;padding:8px;border-radius:4px;}} "
            f"li{{margin-bottom:4px;}}</style>" + html)
        total = len(TUTORIAL_PAGES)
        self._page_label.setText(f"{self._page + 1} / {total}  —  {title}")
        self._prev_btn.setEnabled(self._page > 0)
        self._next_btn.setEnabled(self._page < total - 1)

    def _prev(self):
        if self._page > 0:
            self._page -= 1
            self._show_page()

    def _next(self):
        if self._page < len(TUTORIAL_PAGES) - 1:
            self._page += 1
            self._show_page()


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(420, 380)
        layout = QVBoxLayout(self)

        shortcuts = [
            ("Ctrl+N", "New file"),
            ("Ctrl+O", "Open file"),
            ("Ctrl+Shift+O", "Open directory"),
            ("Ctrl+S", "Save"),
            ("Ctrl+Shift+S", "Save As"),
            ("Ctrl+Q", "Quit"),
            ("Ctrl+F", "Focus search bar"),
            ("Ctrl+Shift+F", "Toggle regex search"),
            ("Ctrl+E", "Export (last format)"),
            ("Ctrl+I", "Import Q3N file"),
            ("Ctrl+W", "New entry wizard"),
            ("Delete", "Delete selected entry"),
            ("F1", "Tutorial"),
            ("F5", "Statistics"),
        ]

        table = QTableWidget(len(shortcuts), 2)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        for i, (key, desc) in enumerate(shortcuts):
            k = QTableWidgetItem(key)
            k.setFont(QFont("monospace"))
            table.setItem(i, 0, k)
            table.setItem(i, 1, QTableWidgetItem(desc))
        layout.addWidget(table)

        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(_load_stylesheet())
        self._file_path = None
        self._modified = False
        if _ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))
        self._all_entries = []  # unfiltered master list
        self._plugin_panels = {}
        self._plugin_dock = None
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()

    def _setup_ui(self):
        self.setWindowTitle("Q3N Manager")
        self.resize(1000, 650)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search quotes...")
        self._search_input.textChanged.connect(self._apply_filter)
        self._regex_check = QCheckBox("Regex")
        self._regex_check.setToolTip("Use regular expressions (Ctrl+Shift+F)")
        self._regex_check.stateChanged.connect(self._apply_filter)
        self._tag_filter = TagFilterCombo()
        self._tag_filter.changed.connect(self._apply_filter)
        filter_row.addWidget(self._search_input, 1)
        filter_row.addWidget(self._regex_check)
        filter_row.addWidget(self._tag_filter)
        left_layout.addLayout(filter_row)

        self._list_view = QListView()
        self._list_view.setItemDelegate(EntryDelegate())
        self._list_view.setEditTriggers(QListView.NoEditTriggers)
        self._list_view.selectionModel()
        self._model = EntryListModel()
        self._list_view.setModel(self._model)
        self._list_view.selectionModel().currentChanged.connect(self._on_selection)
        left_layout.addWidget(self._list_view, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        add_btn = QPushButton("+ New")
        add_btn.clicked.connect(self._add_entry)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self._delete_entry)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        left_layout.addLayout(btn_row)

        splitter.addWidget(left_panel)

        self._detail_view = EntryDetailView()
        self._detail_view.entry_changed.connect(self._on_entry_changed)
        splitter.addWidget(self._detail_view)

        splitter.setSizes([350, 650])
        self.setCentralWidget(splitter)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        self._add_action(file_menu, "&New", "Ctrl+N", self._new_file)
        self._add_action(file_menu, "&Open...", "Ctrl+O", self._open_file)
        self._add_action(file_menu, "Open &Directory...", "Ctrl+Shift+O", self._open_directory)
        file_menu.addSeparator()
        self._add_action(file_menu, "&Save", "Ctrl+S", self._save_file)
        self._add_action(file_menu, "Save &As...", "Ctrl+Shift+S", self._save_as)
        file_menu.addSeparator()
        self._add_action(file_menu, "&Quit", "Ctrl+Q", self.close)

        edit_menu = menubar.addMenu("&Edit")
        self._add_action(edit_menu, "&New Entry...", "Ctrl+W", self._add_entry)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "&Preferences...", None, self._show_settings)

        import_menu = menubar.addMenu("&Import")
        self._add_action(import_menu, "Import Q3N File...", "Ctrl+I", self._import_q3n)
        self._add_action(import_menu, "Import JSON...", None, self._import_json)
        self._add_action(import_menu, "Import Plain Text...", None, self._import_txt)

        export_menu = menubar.addMenu("E&xport")
        self._add_action(export_menu, "Export as Q3N...", None, lambda: self._export('q3n'))
        self._add_action(export_menu, "Export as JSON...", None, lambda: self._export('json'))
        self._add_action(export_menu, "Export as Markdown...", None, lambda: self._export('md'))
        self._add_action(export_menu, "Export as HTML...", None, lambda: self._export('html'))
        self._add_action(export_menu, "Export as Plain Text...", None, lambda: self._export('txt'))
        self._add_action(export_menu, "Export Index...", None, lambda: self._export('index'))
        self._add_action(export_menu, "Export as Fortune...", None, lambda: self._export('fortune'))
        self._add_action(export_menu, "Export as Anki CSV...", None, lambda: self._export('anki'))

        tools_menu = menubar.addMenu("&Tools")
        self._add_action(tools_menu, "Statistics...", "F5", self._show_stats)
        tools_menu.addSeparator()
        self._add_action(tools_menu, "Preview as JSON", None, self._preview_json)
        self._add_action(tools_menu, "Preview as Markdown", None, self._preview_md)
        self._add_action(tools_menu, "Preview Index", None, self._preview_index)
        tools_menu.addSeparator()
        self._add_action(tools_menu, "Generate Index File...", None, self._generate_index_file)
        tools_menu.addSeparator()
        self._add_action(tools_menu, "Validate URIs...", None, self._validate_file)

        view_menu = menubar.addMenu("&View")
        self._view_menu = view_menu
        self._view_menu.setEnabled(False)

        help_menu = menubar.addMenu("&Help")
        self._add_action(help_menu, "&Tutorial...", "F1", self._show_tutorial)
        self._add_action(help_menu, "&Keyboard Shortcuts...", None, self._show_shortcuts)
        help_menu.addSeparator()
        self._add_action(help_menu, "&About Q3N Manager", None, self._show_about)
        self._add_action(help_menu, "About &Qt", None, QApplication.aboutQt)

        for shortcut, slot in [
            ("Ctrl+F", lambda: self._search_input.setFocus()),
            ("Ctrl+Shift+F", lambda: self._regex_check.setChecked(
                not self._regex_check.isChecked())),
            ("Delete", self._delete_entry),
        ]:
            act = QAction(self)
            act.setShortcut(shortcut)
            act.triggered.connect(slot)
            self.addAction(act)

    def _add_action(self, menu, label, shortcut, slot):
        action = QAction(label, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        for label, slot in [("New", self._new_file), ("Open", self._open_file),
                            ("Save", self._save_file), ("+ Entry", self._add_entry)]:
            action = QAction(label, self)
            action.triggered.connect(slot)
            toolbar.addAction(action)

    def _load_entries(self, entries):
        self._all_entries = list(entries)
        self._model.set_entries(self._all_entries)
        self._tag_filter.set_tags(self._all_entries)
        self._detail_view.clear()
        self._status.showMessage(f"{len(entries)} entries loaded")
        self._notify_plugins(self._all_entries)

    def _apply_filter(self):
        search = self._search_input.text()
        tag_filter = self._tag_filter.selected_tag()
        use_regex = self._regex_check.isChecked()

        pat = None
        if search and use_regex:
            try:
                pat = re.compile(search, re.IGNORECASE)
                self._search_input.setStyleSheet("")
            except re.error:
                self._search_input.setStyleSheet("border-color: #e74c3c;")
                pat = None

        def matches(e):
            if tag_filter and e.tag != tag_filter:
                return False
            if search:
                if pat:
                    return bool(pat.search(e.quote) or pat.search(e.uri))
                return (search.lower() in e.quote.lower()
                        or search.lower() in e.uri.lower())
            return True

        filtered = [e for e in self._all_entries if matches(e)]
        self._model.set_entries(filtered)
        self._detail_view.clear()
        self._status.showMessage(f"{len(filtered)} of {len(self._all_entries)} entries")

    def _on_selection(self, current, previous):
        if not current.isValid():
            self._detail_view.clear()
            return
        e = self._model.entry_at(current.row())
        if e:
            self._detail_view.show_entry(current.row(), e)

    def _on_entry_changed(self, row, entry):
        old_entry = self._model.entry_at(row)
        self._model.update_entry(row, entry)
        if old_entry in self._all_entries:
            self._all_entries[self._all_entries.index(old_entry)] = entry
        self._tag_filter.set_tags(self._all_entries)
        self._modified = True
        self._status.showMessage("Entry updated")
        self._notify_plugins(self._all_entries)

    def _add_entry(self):
        wizard = EntryWizard(self)
        if wizard.exec():
            entry = wizard.get_entry()
            self._all_entries.append(entry)
            self._model.add_entry(entry)
            self._tag_filter.set_tags(self._all_entries)
            self._modified = True
            last = self._model.index(self._model.rowCount() - 1)
            self._list_view.selectionModel().setCurrentIndex(
                last, self._list_view.selectionModel().ClearAndSelect)
            self._status.showMessage("Entry added")

    def _delete_entry(self):
        idx = self._list_view.currentIndex()
        if not idx.isValid():
            return
        row = idx.row()
        entry = self._model.entry_at(row)
        if not entry:
            return
        preview = entry.quote[:50].replace('\n', ' ')
        confirm = QMessageBox.question(
            self, "Delete Entry",
            f'Delete this entry?\n"{preview}..."',
            QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            removed = self._model.entry_at(row)
            self._model.remove_entry(row)
            if removed in self._all_entries:
                self._all_entries.remove(removed)
            self._detail_view.clear()
            self._tag_filter.set_tags(self._all_entries)
            self._modified = True
            self._status.showMessage("Entry deleted")

    def _new_file(self):
        if not self._confirm_save():
            return
        self._file_path = None
        self._modified = False
        self._load_entries([])
        self.setWindowTitle("Q3N Manager - New")

    def _open_file(self):
        if not self._confirm_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Q3N File", '',
            "Q3N Files (*.q3n *.q3nt *.quotation *.quotes);;All Files (*)")
        if not path:
            return
        try:
            entries = parse_file(path)
            self._file_path = Path(path)
            self._modified = False
            self._load_entries(entries)
            self.setWindowTitle(f"Q3N Manager - {self._file_path.name}")
            self._status.showMessage(f"Opened {path}")
            self._persist_last_file(self._file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def _save_file(self):
        if self._file_path:
            self._do_save(self._file_path)
        else:
            self._save_as()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Q3N File", '',
            "Q3N Files (*.q3n);;All Files (*)")
        if not path:
            return
        if not path.endswith('.q3n'):
            path += '.q3n'
        self._file_path = Path(path)
        self._do_save(self._file_path)

    def _do_save(self, path):
        try:
            serialize_file(self._all_entries, path)
            self._modified = False
            self.setWindowTitle(f"Q3N Manager - {path.name}")
            self._status.showMessage(f"Saved {len(self._all_entries)} entries to {path}")
            self._persist_last_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _persist_last_file(self, path):
        try:
            from core.config import get_config, save_last_file
            if get_config()['gui'].getboolean('remember_last_file', False):
                save_last_file(path)
        except Exception:
            pass

    def open_path(self, path):
        try:
            entries = parse_file(path)
            self._file_path = Path(path)
            self._modified = False
            self._load_entries(entries)
            self.setWindowTitle(f"Q3N Manager - {self._file_path.name}")
            self._status.showMessage(f"Opened {path}")
            self._persist_last_file(self._file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def _confirm_save(self):
        if not self._modified:
            return True
        ret = QMessageBox.question(
            self, "Unsaved Changes",
            "Save changes?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if ret == QMessageBox.Save:
            self._save_file()
            return True
        return ret == QMessageBox.Discard

    def _import_q3n(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Q3N File", '',
            "Q3N Files (*.q3n *.q3nt);;All Files (*)")
        if not path:
            return
        try:
            entries = parse_file(path)
            for e in entries:
                self._all_entries.append(e)
                self._model.add_entry(e)
            self._tag_filter.set_tags(self._all_entries)
            self._modified = True
            self._status.showMessage(f"Imported {len(entries)} entries from {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed:\n{e}")

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import JSON", '', "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            entries = import_json(path)
            for e in entries:
                self._all_entries.append(e)
                self._model.add_entry(e)
            self._tag_filter.set_tags(self._all_entries)
            self._modified = True
            self._status.showMessage(f"Imported {len(entries)} entries from JSON")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed:\n{e}")

    def _import_txt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Plain Text", '', "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            text = Path(path).read_text(encoding='utf-8')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            url = None
            quote_lines = []
            for line in lines:
                if line.startswith('http://') or line.startswith('https://'):
                    url = line
                else:
                    quote_lines.append(line)
            if not quote_lines:
                QMessageBox.warning(self, "Import", "No quote text found.")
                return
            quote = '\n'.join(quote_lines)
            entry = Q3NEntry(
                uri=url or 'file://' + str(Path(path).resolve()),
                scheme='https' if url and url.startswith('https') else 'file',
                path=url or str(Path(path).resolve()),
                quote=quote,
                tag='imported')
            self._all_entries.append(entry)
            self._model.add_entry(entry)
            self._tag_filter.set_tags(self._all_entries)
            self._modified = True
            self._status.showMessage("Imported plain text")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed:\n{e}")

    def _export(self, fmt):
        entries = self._all_entries
        if not entries:
            QMessageBox.warning(self, "Export", "No entries to export.")
            return
        ext_map = {'q3n': 'q3n', 'json': 'json', 'md': 'md',
                   'html': 'html', 'txt': 'txt', 'index': 'md',
                   'fortune': 'txt', 'anki': 'csv'}
        name_map = {
            'q3n': 'Q3N File', 'json': 'JSON', 'md': 'Markdown',
            'html': 'HTML', 'txt': 'Plain Text', 'index': 'Index',
            'fortune': 'Fortune', 'anki': 'Anki CSV'}
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {name_map[fmt]}", '',
            f"{name_map[fmt]} Files (*.{ext_map[fmt]});;All Files (*)")
        if not path:
            return
        try:
            export_file(entries, path, fmt)
            self._status.showMessage(f"Exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

    def _preview_json(self):
        entries = self._all_entries
        if not entries:
            QMessageBox.warning(self, "Preview", "No entries.")
            return
        content = export_json(entries)
        PreviewDialog("JSON Preview", content, self).exec()

    def _preview_md(self):
        entries = self._all_entries
        if not entries:
            QMessageBox.warning(self, "Preview", "No entries.")
            return
        content = export_markdown(entries)
        PreviewDialog("Markdown Preview", content, self).exec()

    def _preview_index(self):
        entries = self._all_entries
        if not entries:
            QMessageBox.warning(self, "Preview", "No entries.")
            return
        content = generate_index(entries)
        PreviewDialog("Index Preview", content, self).exec()

    def _generate_index_file(self):
        entries = self._all_entries
        if not entries:
            QMessageBox.warning(self, "Index", "No entries to index.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Index", '', "Markdown (*.md);;All Files (*)")
        if not path:
            return
        try:
            export_file(entries, path, 'index')
            self._status.showMessage(f"Index saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save index:\n{e}")

    def _validate_file(self):
        from core.q3n import validate_uri
        if not self._all_entries:
            QMessageBox.information(self, "Validate URIs", "No entries loaded.")
            return
        invalid = []
        for i, entry in enumerate(self._all_entries, 1):
            errs = validate_uri(entry.uri)
            if errs:
                short = entry.uri[:60] + ('…' if len(entry.uri) > 60 else '')
                invalid.append(f'Entry {i}: {errs[0]}\n  {short}')
        if not invalid:
            QMessageBox.information(self, "Validate URIs",
                f"All {len(self._all_entries)} URIs are valid.")
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Validate URIs")
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"{len(invalid)} of {len(self._all_entries)} entries have invalid URIs.")
            msg.setDetailedText('\n\n'.join(invalid))
            msg.exec()

    def load_plugins(self, manager):
        panels = manager.panels
        if not panels:
            return
        tab_widget = QTabWidget()
        for name, widget_class in panels.items():
            widget = widget_class(self)
            self._plugin_panels[name] = widget
            tab_widget.addTab(widget, name.title())
        dock = QDockWidget("Plugins", self)
        dock.setWidget(tab_widget)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self._plugin_dock = dock
        self._view_menu.setEnabled(True)
        self._view_menu.addAction(dock.toggleViewAction())

    def _notify_plugins(self, entries):
        for widget in self._plugin_panels.values():
            if hasattr(widget, 'set_entries'):
                widget.set_entries(entries)

    def _open_directory(self):
        if not self._confirm_save():
            return
        path = QFileDialog.getExistingDirectory(self, "Open Q3N Directory", '')
        if not path:
            return
        try:
            from core.q3n import list_entries
            results = list_entries(path)
            if not results:
                QMessageBox.information(self, "Open Directory",
                    "No Q3N files found in that directory.")
                return
            all_entries = [e for _, entries in results for e in entries]
            self._file_path = None
            self._modified = False
            self._load_entries(all_entries)
            n_files = len(results)
            self.setWindowTitle(
                f"Q3N Manager - {Path(path).name}/ ({n_files} file{'s' if n_files != 1 else ''})")
            self._status.showMessage(
                f"Loaded {len(all_entries)} entries from {n_files} files")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open directory:\n{e}")

    def _show_stats(self):
        StatsDialog(self._all_entries, self).exec()

    def _show_settings(self):
        SettingsDialog(self).exec()

    def _show_tutorial(self):
        TutorialDialog(self).exec()

    def _show_shortcuts(self):
        ShortcutsDialog(self).exec()

    def _show_about(self):
        QMessageBox.about(self, "About Q3N Manager",
            "<h2>Q3N Manager</h2>"
            f"<p>Version {__version__}</p>"
            "<p>A graphical browser and editor for Q3N "
            "(Quote Triple-Slash Notation) files.</p>"
            "<p>Q3N is a plain-text file format for storing "
            "quotations, citations, and annotated excerpts "
            "with source URIs.</p>"
            "<hr>"
            "<p style='font-size:11px;color:#888;'>"
            "License: AGPL-3.0 with Anti-Fascist Exception</p>")

    def closeEvent(self, event):
        if not self._confirm_save():
            event.ignore()
            return
        event.accept()
