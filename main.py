import sys
import os
sys.path.insert(0, os.path.abspath("src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app import TheiaApp
from controllers.application_controller import ApplicationController
from pathlib import Path

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path("assets/icon.jpg"))))
    window = TheiaApp()
    controller = ApplicationController(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
