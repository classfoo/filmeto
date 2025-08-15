import asyncio
import os
import sys

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from app.app import App
from app.ui.main_window import MainWindow


if __name__ == "__main__":
    main_path = os.path.abspath(os.path.dirname(__file__))
    app = App(main_path)
    app.start()
