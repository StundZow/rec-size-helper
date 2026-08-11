"""Glassmorphism installer for Rec Size Helper.

Built as its own PyInstaller onefile exe with the application binary and the
uninstaller embedded as payload (see release.py). Per-user install: no admin
rights needed, which also lets the app's auto-updater replace its own exe.
"""
from __future__ import annotations

import os
import subprocess
import sys
import winreg
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rechelper import theme
from rechelper.__version__ import VERSION
from rechelper.glass_background import GlassBackground
from rechelper.resources import resource_path
from rechelper.style import build_stylesheet

APP_NAME = "Rec Size Helper"
EXE_NAME = "RecSizeHelper.exe"
UNINSTALL_NAME = "uninstall.exe"
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\RecSizeHelper"

_CREATE_NO_WINDOW = 0x08000000


def payload_path(name: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "payload" / name
    return Path(__file__).resolve().parent.parent / "dist" / name


def default_install_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "RecSizeHelper"


def start_menu_dir() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def desktop_dir() -> Path:
    import ctypes.wintypes

    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x0000, None, 0, buf)  # CSIDL_DESKTOP
    return Path(buf.value)


def make_shortcut(lnk_path: Path, target: Path, workdir: Path):
    import win32com.client

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(lnk_path))
    shortcut.TargetPath = str(target)
    shortcut.WorkingDirectory = str(workdir)
    shortcut.IconLocation = str(target)
    shortcut.Description = APP_NAME
    shortcut.Save()


class InstallWorker(QThread):
    progress = Signal(int, int)
    status = Signal(str)
    done = Signal()
    failed = Signal(str)

    def __init__(self, install_dir: Path, desktop_icon: bool):
        super().__init__()
        self.install_dir = install_dir
        self.desktop_icon = desktop_icon

    def run(self):
        try:
            self.status.emit("Fermeture de l'application si elle est ouverte…")
            subprocess.run(
                ["taskkill", "/F", "/IM", EXE_NAME],
                capture_output=True, creationflags=_CREATE_NO_WINDOW,
            )

            self.status.emit("Copie des fichiers…")
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self._copy_with_progress(payload_path(EXE_NAME), self.install_dir / EXE_NAME)
            uninstall_src = payload_path(UNINSTALL_NAME)
            if uninstall_src.exists():
                self._copy_with_progress(uninstall_src, self.install_dir / UNINSTALL_NAME)

            self.status.emit("Création des raccourcis…")
            menu_dir = start_menu_dir()
            menu_dir.mkdir(parents=True, exist_ok=True)
            make_shortcut(menu_dir / f"{APP_NAME}.lnk", self.install_dir / EXE_NAME, self.install_dir)
            if (self.install_dir / UNINSTALL_NAME).exists():
                make_shortcut(
                    menu_dir / f"Désinstaller {APP_NAME}.lnk",
                    self.install_dir / UNINSTALL_NAME, self.install_dir,
                )
            if self.desktop_icon:
                make_shortcut(desktop_dir() / f"{APP_NAME}.lnk", self.install_dir / EXE_NAME, self.install_dir)

            self.status.emit("Enregistrement dans Windows…")
            self._register_uninstall()

            self.done.emit()
        except Exception as e:
            self.failed.emit(str(e))

    def _copy_with_progress(self, src: Path, dst: Path):
        total = src.stat().st_size
        copied = 0
        with open(src, "rb") as fin, open(dst, "wb") as fout:
            while True:
                chunk = fin.read(1024 * 1024)
                if not chunk:
                    break
                fout.write(chunk)
                copied += len(chunk)
                self.progress.emit(copied, total)

    def _register_uninstall(self):
        exe = self.install_dir / EXE_NAME
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
        try:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "StundZow")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(self.install_dir / UNINSTALL_NAME))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            if exe.exists():
                winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, exe.stat().st_size // 1024)
        finally:
            winreg.CloseKey(key)


class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Installation — {APP_NAME}")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.setFixedSize(680, 560)
        self._worker: InstallWorker | None = None
        self._installed = False

        self.palette_dict = theme.get_palette(theme.detect_windows_theme())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        background = GlassBackground()
        background.set_theme(self.palette_dict)
        outer.addWidget(background)

        root = QVBoxLayout(background)
        root.setContentsMargins(40, 36, 40, 30)
        root.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(18)
        logo = QLabel()
        pixmap = QPixmap(resource_path("assets/icon.png"))
        logo.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        subtitle = QLabel(f"Assistant d'installation — version {VERSION}")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 24, 26, 24)
        card_layout.setSpacing(16)

        path_label = QLabel("Dossier d'installation")
        path_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        card_layout.addWidget(path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_edit = QLineEdit(str(default_install_dir()))
        path_row.addWidget(self.path_edit, stretch=1)
        browse = QPushButton("Parcourir…")
        browse.setObjectName("pathButton")
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self.pick_folder)
        path_row.addWidget(browse)
        card_layout.addLayout(path_row)

        card_layout.addSpacing(6)

        self.desktop_check = QCheckBox("Créer une icône sur le Bureau")
        self.desktop_check.setChecked(True)
        self.desktop_check.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.desktop_check)

        self.launch_check = QCheckBox("Lancer Rec Size Helper après l'installation")
        self.launch_check.setChecked(True)
        self.launch_check.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.launch_check)

        root.addWidget(card)
        root.addStretch()

        self.status_label = QLabel("Prêt à installer.")
        self.status_label.setObjectName("mutedText")
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        root.addWidget(self.progress_bar)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("pathButton")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.close)
        buttons.addWidget(self.cancel_button)

        self.install_button = QPushButton("⬇️  Installer")
        self.install_button.setObjectName("updateButton")
        self.install_button.setCursor(Qt.PointingHandCursor)
        self.install_button.clicked.connect(self.on_main_button)
        buttons.addWidget(self.install_button)
        root.addLayout(buttons)

        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setDuration(300)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self._fade.start()

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier d'installation", self.path_edit.text())
        if folder:
            self.path_edit.setText(str(Path(folder) / "RecSizeHelper"))

    def on_main_button(self):
        if self._installed:
            if self.launch_check.isChecked():
                exe = Path(self.path_edit.text()) / EXE_NAME
                subprocess.Popen([str(exe)], cwd=str(exe.parent), close_fds=True)
            self.close()
            return

        self.install_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.path_edit.setEnabled(False)
        self.desktop_check.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self._worker = InstallWorker(Path(self.path_edit.text()), self.desktop_check.isChecked())
        self._worker.progress.connect(self.on_progress)
        self._worker.status.connect(self.status_label.setText)
        self._worker.done.connect(self.on_done)
        self._worker.failed.connect(self.on_failed)
        self._worker.start()

    def on_progress(self, done: int, total: int):
        if total:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(done)

    def on_done(self):
        self._installed = True
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.status_label.setText("✅  Installation terminée !")
        self.install_button.setText("Terminer")
        self.install_button.setEnabled(True)

    def on_failed(self, message: str):
        self.status_label.setText(f"❌  Échec de l'installation : {message}")
        self.progress_bar.setVisible(False)
        self.install_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.path_edit.setEnabled(True)
        self.desktop_check.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    palette = theme.get_palette(theme.detect_windows_theme())
    app.setStyleSheet(build_stylesheet(palette))
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
