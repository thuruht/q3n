from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QTextEdit, QComboBox,
                               QRadioButton, QGroupBox, QFormLayout, QMessageBox)
from PySide6.QtCore import Qt
from core.q3n import Q3NEntry, parse_scheme

SOURCE_TYPES = {
    "Web URL (https)": ("https", "https://"),
    "Web URL (http)": ("http", "http://"),
    "Local File": ("file", "file://"),
    "Book (ISBN)": ("isbn", "isbn://"),
    "Academic Paper (DOI)": ("doi", "doi://"),
    "arXiv Paper": ("arxiv", "arxiv://"),
    "Person / Contact": ("q3n", "q3n://"),
    "YouTube Video": ("yt", "yt://"),
    "Map Location (OSM)": ("osm", "osm://"),
    "Geographic Coordinates": ("geo", "geo:"),
    "Overpass Query": ("overpass", "overpass://"),
    "Custom URI": ("custom", ""),
}

TAG_PRESETS = [
    "",
    "cite/article",
    "cite/book",
    "cite/interview",
    "cite/speech",
    "cite/lecture",
    "cite/podcast",
    "note/research",
    "note/personal",
    "note/idea",
    "note/summary",
    "ref/academic",
    "ref/technical",
    "place/landmark",
    "place/location",
    "place/route",
]


class SourceTypePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Source Type")
        self.setSubTitle("What kind of source is this quote from?")
        layout = QVBoxLayout(self)

        self._combo = QComboBox()
        for label in SOURCE_TYPES:
            self._combo.addItem(label)
        self._combo.currentIndexChanged.connect(self._on_change)
        layout.addWidget(self._combo)

        self._uri_preview = QLabel()
        self._uri_preview.setStyleSheet("color: #666; padding: 8px;")
        layout.addWidget(self._uri_preview)
        layout.addStretch()

    def _on_change(self):
        label = self._combo.currentText()
        scheme, prefix = SOURCE_TYPES[label]
        sep = ':' if prefix.endswith(':') and '://' not in prefix else '://'
        self._uri_preview.setText(f"URI scheme: {scheme}{sep}\nExample prefix: {prefix}")
        self.setField("scheme", scheme)
        self.setField("uri_prefix", prefix)

    def initializePage(self):
        self._on_change()


class SourceDetailsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Source Details")
        self.setSubTitle("Enter the source identifier for this quote.")

        layout = QVBoxLayout(self)
        self._help_label = QLabel()
        self._help_label.setWordWrap(True)
        self._help_label.setStyleSheet("color: #555; padding-bottom: 8px;")
        layout.addWidget(self._help_label)

        form = QFormLayout()
        self._uri_input = QLineEdit()
        self._uri_input.setPlaceholderText("")
        form.addRow("URI:", self._uri_input)
        layout.addLayout(form)

        self._help_detail = QLabel()
        self._help_detail.setWordWrap(True)
        self._help_detail.setStyleSheet("color: #888; font-size: 11px; padding-top: 4px;")
        layout.addWidget(self._help_detail)
        layout.addStretch()

        self.registerField("uri*", self._uri_input)

    def initializePage(self):
        scheme = self.field("scheme")
        prefix = self.field("uri_prefix")
        self._uri_input.setText(prefix)
        help_texts = {
            "https": "Enter the full URL of the web page.\ne.g. https://example.com/article-title",
            "http": "Enter the full URL of the web page.",
            "file": "Enter the path to the file.\ne.g. file:///home/user/notes.txt#line=42",
            "isbn": "Enter ISBN and optional details.\nisbn://ISBN;'Title';'Author';Year",
            "doi": "Enter the DOI identifier.\ndoi://10.1234/abcd.567",
            "arxiv": "Enter the arXiv ID.\narxiv://2305.12345",
            "q3n": "Enter person reference.\nq3n://handle:@id;email;'Name'",
            "yt": "Enter YouTube video ID.\nyt://dQw4w9WgXcQ",
            "osm": "Enter OpenStreetMap object type and ID.\nosm://node/12345  or  osm://way/67890  or  osm://relation/999",
            "geo": "Enter latitude and longitude (optional zoom).\ngeo:51.5074,-0.1278  or  geo:48.8566,2.3522?z=15",
            "overpass": "Enter an Overpass API query.\noverpass://node[amenity=cafe](51.4,0.0,51.6,0.2)",
            "custom": "Enter any custom URI.",
        }
        self._help_label.setText(help_texts.get(scheme, "Enter the source URI."))

    def isComplete(self):
        uri = self._uri_input.text().strip()
        if not uri:
            return False
        prefix = self.field("uri_prefix")
        if prefix and not uri.startswith(prefix):
            return False
        return len(uri) > len(prefix)


class TagPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Categorization")
        self.setSubTitle("Add a tag to categorize this entry.")

        layout = QVBoxLayout(self)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        for t in TAG_PRESETS:
            self._combo.addItem(t)
        self._combo.setCurrentText("")
        self._combo.currentTextChanged.connect(self._on_change)
        layout.addWidget(QLabel("Tag (optional):"))
        layout.addWidget(self._combo)

        self._desc_label = QLabel(
            "Tags help categorize and filter entries.\n"
            "Use a slash for hierarchy, e.g. cite/article or note/research.")
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet("color: #888; font-size: 11px; padding-top: 4px;")
        layout.addWidget(self._desc_label)
        layout.addStretch()

        self.registerField("tag", self._combo, "currentText")

    def _on_change(self, text):
        pass


class ContentPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Quote Content")
        self.setSubTitle("Enter the quoted text.")

        layout = QVBoxLayout(self)
        self._quote_input = QTextEdit()
        self._quote_input.setPlaceholderText(
            "Paste or type the quoted text here...\n\n"
            "This can be multiple paragraphs.")
        self._quote_input.setMinimumHeight(200)
        layout.addWidget(self._quote_input)

        self.registerField("quote*", self._quote_input, "plainText")


class ReviewPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Review")
        self.setSubTitle("Preview the entry before saving.")

        layout = QVBoxLayout(self)
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setStyleSheet("font-family: monospace; background: #f5f5f5;")
        layout.addWidget(self._preview)

    def initializePage(self):
        parts = []
        parts.append("#!q3n-format\n")
        tag = self.field("tag")
        uri = self.field("uri")
        tag_part = f" /// {tag}:" if tag else ""
        parts.append(f"/// {uri}{tag_part}")
        parts.append(self.field("quote"))
        parts.append("\\\\\\")
        self._preview.setPlainText('\n'.join(parts))


class EntryWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Q3N Entry")
        self.setMinimumSize(600, 500)
        self.setWizardStyle(QWizard.ModernStyle)

        self.addPage(SourceTypePage())
        self.addPage(SourceDetailsPage())
        self.addPage(TagPage())
        self.addPage(ContentPage())
        self.addPage(ReviewPage())

    def get_entry(self):
        uri = self.field("uri").strip()
        tag = self.field("tag").strip() or None
        quote = self.field("quote").strip()
        scheme, path = parse_scheme(uri)
        return Q3NEntry(uri, scheme, path, quote, tag)
