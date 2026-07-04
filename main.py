import sys
import os
sys.path.insert(0, os.path.abspath("src"))

from PyQt6.QtWidgets import QApplication
from app import TheiaApp
from controllers.application_controller import ApplicationController

def main():
    app = QApplication(sys.argv)
    window = TheiaApp()
    controller = ApplicationController(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
