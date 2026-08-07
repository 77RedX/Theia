"""Centralized Icon Manager for Theia."""

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from pathlib import Path
import os
import sys

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        # Assuming this is in utils/ and root is one level up
        base_path = Path(__file__).parent.parent.resolve()
    return base_path / relative_path

class IconManager:
    """Manages icon loading, caching, and serving."""
    
    _cache = {}
    
    @classmethod
    def get_icon(cls, name: str) -> QIcon:
        """Get an icon by name (e.g. 'play.svg'). Cached for performance."""
        if name in cls._cache:
            return cls._cache[name]
            
        icon_path = get_resource_path(f"assets/{name}")
        if not icon_path.exists():
            # Return empty icon if not found to prevent crashes
            return QIcon()
            
        icon = QIcon(str(icon_path))
        cls._cache[name] = icon
        return icon
