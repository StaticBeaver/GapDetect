# icons.py
# -*- coding: utf-8 -*-
"""
Theme-colored vector icons (qtawesome / Font Awesome) used instead of emoji
icons, with a dedicated per-app cache folder.

- icon(): returns a QIcon for things like QPushButton.setIcon().
- pixmap(): returns a QPixmap directly (e.g. QLabel.setPixmap()).
"""
import os
import sys
import qtawesome as qta
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

_CACHE_DIR = os.path.join(
    os.environ.get('APPDATA', os.path.expanduser('~')),
    'GapDetect', 'icon_cache',
)

# When bundled with PyInstaller --onefile, files are extracted to a temporary
# folder under sys._MEIPASS; in development, the project root is used.
_BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))


def asset_path(name):
    return os.path.join(_BASE_DIR, 'assets', name)


def app_icon():
    """Returns assets/icon.ico for the window/taskbar icon."""
    return QIcon(asset_path('icon.ico'))


def logo_pixmap(height=22):
    """Scales assets/LOGO.png (header brand logo) to the given height,
    keeping the aspect ratio."""
    pm = QPixmap(asset_path('LOGO.png'))
    return pm.scaledToHeight(height, Qt.SmoothTransformation)


def icon(name, color, size=None):
    """Returns a QIcon for widgets like QPushButton/QAction."""
    if size:
        return qta.icon(name, color=color, options=[{'scale_factor': size}])
    return qta.icon(name, color=color)


def pixmap(name, color, size=24):
    """Returns a QPixmap directly, for things like QLabel.setPixmap()."""
    return qta.icon(name, color=color).pixmap(size, size)


def icon_file(name, color, size=18):
    """Returns a PNG file path for QSS 'image: url(...)' (renders and caches it)."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    key = f"{name.replace('.', '_')}_{color.lstrip('#')}_{size}.png"
    path = os.path.join(_CACHE_DIR, key)
    if not os.path.exists(path):
        qta.icon(name, color=color).pixmap(size, size).save(path, "PNG")
    return path.replace("\\", "/")
