"""Uninstall flow for Rec Size Helper, in the app's flat style.

Runs inside the *same* exe as the app itself (invoked as
`RecSizeHelper.exe --uninstall`) so the installer only has to embed one
onefile payload instead of a whole second copy of the Qt runtime just for
this confirmation dialog.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from . import icons, theme
from .glass_background import GlassBackground
from .resources import resource_path
from .style import build_stylesheet
from .widgets import button, note

APP_NAME = "Rec Size Helper"
EXE_NAME = "RecSizeHelper.exe"
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\RecSizeHelper"

_CREATE_NO_WINDOW = 0x08000000


def start_menu_dir() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def desktop_shortcut() -> Path:
    import ctypes.wintypes

    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x0000, None, 0, buf)
    return Path(buf.value) / f"{APP_NAME}.lnk"


def do_uninstall() -> None:
    install_dir = Path(sys.executable).resolve().parent

    subprocess.run(["taskkill", "/F", "/IM", EXE_NAME],
                   capture_output=True, creationflags=_CREATE_NO_WINDOW)

    shutil.rmtree(start_menu_dir(), ignore_errors=True)
    try:
        desktop_shortcut().unlink(missing_ok=True)
    except OSError:
        pass

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
    except OSError:
        pass

    # The folder (including this exe) is removed after we exit — an exe can't
    # delete itself while running. Retried for a while: a file just written to
    # disk (this exe, minutes ago) can still be briefly held by antivirus
    # real-time scanning, which would otherwise make a single rmdir attempt
    # fail and abandon the whole tree.
    pid = os.getpid()
    bat_path = Path(tempfile.gettempdir()) / "rec_size_helper_uninstall.bat"
    bat_path.write_text(
        f"""@echo off
:waitproc
tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL
if %errorlevel%==0 (
    timeout /t 1 /nobreak >nul
    goto waitproc
)

set RETRY=0
:tryremove
rmdir /s /q "{install_dir}" 2>nul
if exist "{install_dir}" (
    set /a RETRY+=1
    if %RETRY% LSS 90 (
        timeout /t 1 /nobreak >nul
        goto tryremove
    )
)
del "%~f0"
""",
        encoding="utf-8",
    )
    subprocess.Popen(["cmd", "/c", str(bat_path)],
                     creationflags=_CREATE_NO_WINDOW, close_fds=True)


class UninstallWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Désinstaller {APP_NAME}")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.setFixedSize(520, 300)
        palette = theme.get_palette(theme.detect_windows_theme())
        icons.set_palette(palette)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        background = GlassBackground()
        background.set_theme(palette)
        outer.addWidget(background)

        root = QVBoxLayout(background)
        root.setContentsMargins(34, 30, 34, 26)
        root.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(16)
        logo = QLabel()
        pixmap = QPixmap(resource_path("assets/icon.png")).scaled(104, 104, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap.setDevicePixelRatio(2.0)
        logo.setPixmap(pixmap)
        header.addWidget(logo)
        title = QLabel(f"Désinstaller {APP_NAME} ?")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        root.addWidget(note(
            "L'application et ses raccourcis seront supprimés.<br>"
            "Vos enregistrements vidéo ne seront évidemment pas touchés."
        ))
        root.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(button("Annuler", on_click=self.close))
        buttons.addWidget(button("Désinstaller", "trash", "primary", self.on_confirm))
        root.addLayout(buttons)

    def on_confirm(self):
        do_uninstall()
        self.close()


def run_uninstall():
    app = QApplication(sys.argv)
    palette = theme.get_palette(theme.detect_windows_theme())
    app.setStyleSheet(build_stylesheet(palette))
    window = UninstallWindow()
    window.show()
    sys.exit(app.exec())
