import sys
import os
sys.path.insert(0, os.path.abspath("src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app import TheiaApp
from controllers.application_controller import ApplicationController
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent.resolve() / relative_path

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(get_resource_path("app_icon.ico"))))
    window = TheiaApp()
    controller = ApplicationController(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
