"""Fortune desktop widget — always-on-top overlay that cycles through quotes.

Features:
    - Stay-on-top desktop overlay
    - Configurable transparency (30–100%)
    - Adjustable refresh interval (10s – 30min)
    - Click-through mode (pass clicks to underlying windows)
    - Category-based filtering
    - ASCII art display alongside the quote
"""

from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                               QPushButton, QSlider, QSpinBox, QCheckBox,
                               QDialog, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPalette, QAction

import sys
_repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from core.q3n import parse_file, list_entries
from core.fortune import display_fortune


class FortuneOverlay(QWidget):
    """Floating desktop widget that displays random Q3N fortunes."""

    def __init__(self, entries=None, parent=None):
        super().__init__(parent)
        self._entries = entries or []
        self._interval_ms = 60000  # Default 60 seconds
        self._opacity = 0.85
        self._click_through = False
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        self.setWindowTitle('Q3N Fortune')
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.setStyleSheet("""
            QWidget#fortuneContainer {
                background: rgba(30, 30, 30, 220);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 12px;
                padding: 12px;
            }
            QLabel#fortuneText {
                color: #e0e0e0;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                padding: 8px;
            }
            QLabel#attributionText {
                color: #999;
                font-size: 11px;
                padding: 4px 8px 0 8px;
            }
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-size: 16px;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: #fff;
                background: rgba(255, 255, 255, 30);
                border-radius: 4px;
            }
        """)

        container = QWidget(self)
        container.setObjectName('fortuneContainer')
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        # Controls row
        ctrl_row = QHBoxLayout()
        self._art_label = QLabel('🎲')
        self._art_label.setStyleSheet('font-size: 14px;')
        self._refresh_btn = QPushButton('↻')
        self._refresh_btn.setToolTip('New fortune')
        self._refresh_btn.clicked.connect(self.show_random)
        self._settings_btn = QPushButton('⚙')
        self._settings_btn.setToolTip('Settings')
        self._settings_btn.clicked.connect(self._show_settings)
        ctrl_row.addWidget(self._art_label)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self._refresh_btn)
        ctrl_row.addWidget(self._settings_btn)
        layout.addLayout(ctrl_row)

        # Fortune text
        self._fortune_label = QLabel('Open a Q3N file to begin')
        self._fortune_label.setObjectName('fortuneText')
        self._fortune_label.setWordWrap(True)
        layout.addWidget(self._fortune_label)

        # Attribution
        self._attribution_label = QLabel('')
        self._attribution_label.setObjectName('attributionText')
        layout.addWidget(self._attribution_label)

        self.setCentralWidget(container)
        self.set_opacity(self._opacity)
        self.resize(380, 220)
        self._position_at_corner()

    def setCentralWidget(self, widget):
        """Use an outer layout so the container is the sole child."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(widget)

    def _setup_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.show_random)
        self._timer.start(self._interval_ms)

    def _position_at_corner(self):
        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.width() - self.width() - 20,
                      geo.height() - self.height() - 40)

    def set_opacity(self, value):
        self._opacity = max(0.3, min(1.0, value))
        self.setWindowOpacity(self._opacity)

    def set_click_through(self, enabled):
        self._click_through = enabled
        if enabled:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def set_entries(self, entries):
        self._entries = entries
        self.show_random()

    def show_random(self):
        if self._entries:
            text = display_fortune(self._entries)
            parts = text.split('\n', 1)
            if len(parts) > 1:
                art, rest = parts
                self._art_label.setText(art.strip()[:4])
                rest_lines = rest.split('\n')
                quote_lines = [l for l in rest_lines if not l.startswith('—')]
                attr_line = next((l for l in rest_lines if l.startswith('—')), '')
                self._fortune_label.setText('\n'.join(quote_lines).strip())
                self._attribution_label.setText(attr_line)
            else:
                self._fortune_label.setText(text)
                self._attribution_label.setText('')

    def _show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Fortune Settings')
        layout = QFormLayout(dialog)

        # Interval
        interval_spin = QSpinBox()
        interval_spin.setRange(10, 1800)
        interval_spin.setValue(self._interval_ms // 1000)
        interval_spin.setSuffix(' sec')
        layout.addRow('Interval:', interval_spin)

        # Opacity
        opacity_slider = QSlider(Qt.Horizontal)
        opacity_slider.setRange(30, 100)
        opacity_slider.setValue(int(self._opacity * 100))
        layout.addRow('Opacity:', opacity_slider)

        # Click-through
        click_cb = QCheckBox('Pass clicks through')
        click_cb.setChecked(self._click_through)
        layout.addRow(click_cb)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec():
            self._interval_ms = interval_spin.value() * 1000
            self._timer.setInterval(self._interval_ms)
            self.set_opacity(opacity_slider.value() / 100.0)
            self.set_click_through(click_cb.isChecked())

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if not self._click_through:
            self.windowHandle().startSystemMove()
        super().mousePressEvent(event)
