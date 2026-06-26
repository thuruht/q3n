#!/usr/bin/env python3
"""Entry point for the Q3N GUI when installed system-wide."""
import sys
import os

# When installed via deb/pip, the gui package is on the path
from gui.main_window import MainWindow
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Q3N Manager")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
