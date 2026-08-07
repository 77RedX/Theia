import sys
import os
from pathlib import Path

# Add src to python path
sys.path.insert(0, os.path.abspath("src"))

# Set Windows AppUserModelID so taskbar displays custom app_icon.ico
if sys.platform == 'win32':
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('theia.video.enhancer.desktop.1.0')
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app import TheiaApp
from controllers.application_controller import ApplicationController

def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent.resolve() / relative_path

def main():
    app = QApplication(sys.argv)
    icon_path = get_resource_path("app_icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
    window = TheiaApp()
    controller = ApplicationController(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
