"""Glassmorphism uninstaller for Rec Size Helper.

Ships inside the install directory. Removes shortcuts and the registry entry,
then hands the folder deletion to a detached script (an exe cannot delete
itself while running).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rechelper import theme
from rechelper.glass_background import GlassBackground
from rechelper.resources import resource_path
from rechelper.style import build_stylesheet

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
    # delete itself while running. Retried a few times: a file just written to
    # disk (this uninstaller, minutes ago) can still be briefly held by
    # antivirus real-time scanning, which would otherwise make a single
    # rmdir attempt fail and abandon the whole tree.
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
    if %RETRY% LSS 40 (
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
        pixmap = QPixmap(resource_path("assets/icon.png"))
        logo.setPixmap(pixmap.scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)
        title = QLabel(f"Désinstaller {APP_NAME} ?")
        title.setStyleSheet("font-size: 19px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 18, 22, 18)
        info = QLabel(
            "L'application et ses raccourcis seront supprimés.\n"
            "Vos enregistrements vidéo ne seront évidemment pas touchés."
        )
        info.setObjectName("mutedText")
        info.setWordWrap(True)
        card_layout.addWidget(info)
        root.addWidget(card)
        root.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Annuler")
        cancel.setObjectName("pathButton")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.close)
        buttons.addWidget(cancel)

        confirm = QPushButton("🗑️  Désinstaller")
        confirm.setObjectName("deleteButton")
        confirm.setCursor(Qt.PointingHandCursor)
        confirm.clicked.connect(self.on_confirm)
        buttons.addWidget(confirm)
        root.addLayout(buttons)

    def on_confirm(self):
        do_uninstall()
        self.close()


def main():
    app = QApplication(sys.argv)
    palette = theme.get_palette(theme.detect_windows_theme())
    app.setStyleSheet(build_stylesheet(palette))
    window = UninstallWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
