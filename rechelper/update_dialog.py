from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from . import theme
from .__version__ import VERSION
from .glass_background import GlassBackground
from .resources import ICON_PATH
from .updater import DownloadWorker, UpdateInfo, launch_self_update


class UpdateDialog(QDialog):
    def __init__(self, info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("Mise à jour disponible")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setMinimumWidth(460)
        self.setModal(True)
        self._worker: DownloadWorker | None = None

        # same frosted-gradient backdrop as the main window
        palette = getattr(parent, "palette", None)
        if not isinstance(palette, dict):
            palette = theme.get_palette(theme.detect_windows_theme())
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        background = GlassBackground()
        background.set_theme(palette)
        outer.addWidget(background)

        root = QVBoxLayout(background)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(14)
        icon_label = QLabel("🚀")
        icon_label.setStyleSheet("font-size: 34px;")
        header.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Nouvelle version disponible")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        subtitle = QLabel(f"v{VERSION} → v{info.version}")
        subtitle.setObjectName("mutedText")
        subtitle.setStyleSheet("font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        root.addLayout(header)

        if info.notes.strip():
            notes = QTextEdit()
            notes.setReadOnly(True)
            notes.setPlainText(info.notes.strip())
            notes.setMaximumHeight(140)
            notes.setObjectName("updateNotes")
            root.addWidget(notes)

        self.status_label = QLabel("Prêt à installer.")
        self.status_label.setObjectName("mutedText")
        self.status_label.setStyleSheet("font-size: 12px;")
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.later_button = QPushButton("Plus tard")
        self.later_button.setObjectName("pathButton")
        self.later_button.clicked.connect(self.reject)
        button_row.addWidget(self.later_button)

        self.install_button = QPushButton("⬇️  Installer maintenant")
        self.install_button.setObjectName("updateButton")
        self.install_button.clicked.connect(self.start_download)
        button_row.addWidget(self.install_button)
        root.addLayout(button_row)

    def start_download(self):
        self.install_button.setEnabled(False)
        self.later_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Téléchargement…")

        current_exe = Path(sys.executable)
        dest = current_exe.parent / f"{current_exe.stem}.new.exe"

        self._worker = DownloadWorker(self.info.download_url, dest)
        self._worker.progress.connect(self.on_progress)
        self._worker.finished_download.connect(self.on_download_finished)
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_progress(self, done: int, total: int):
        if total:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(done)
            mb_done = done / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(f"Téléchargement… {mb_done:.0f} / {mb_total:.0f} Mo")

    def on_download_finished(self, path: str):
        self.status_label.setText("Installation… l'application va redémarrer.")
        self.progress_bar.setRange(0, 0)
        launch_self_update(Path(path))
        QApplication.instance().quit()

    def on_error(self, message: str):
        self.status_label.setText(f"Échec de la mise à jour : {message}")
        self.install_button.setEnabled(True)
        self.later_button.setEnabled(True)
        self.progress_bar.setVisible(False)
