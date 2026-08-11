from __future__ import annotations

import math
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from . import settings, theme
from .models import Recording
from .resources import ICON_PATH
from .storage_bar import StorageBar
from .style import build_stylesheet
from .timeline_widget import TimelineWidget
from .update_dialog import UpdateDialog
from .updater import UpdateCheckWorker, is_frozen
from .worker import ScanWorker

MKV_COLOR = "#ef4444"
MP4_COLOR = "#3b82f6"
OTHER_COLOR = "#8b5cf6"
FREE_COLOR = "#9aa3b5"


def format_size(num_bytes: float) -> str:
    gb = num_bytes / (1024**3)
    if gb >= 0.1:
        return f"{gb:.1f} Go".replace(".", ",")
    mb = num_bytes / (1024**2)
    return f"{mb:.0f} Mo"


def _legend_dot(color: str, text: str) -> QLabel:
    label = QLabel(f"●  {text}")
    label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")
    return label


class PinnedChip(QFrame):
    clicked = Signal(str)
    unpinned = Signal(str)
    move_left = Signal(str)
    move_right = Signal(str)

    def __init__(self, path: str, is_first: bool, is_last: bool):
        super().__init__()
        self.path = path
        self.setObjectName("pinChip")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        left_button = QPushButton("◀")
        left_button.setObjectName("pinChipMove")
        left_button.setFixedSize(18, 20)
        left_button.setToolTip("Déplacer vers la gauche")
        left_button.setCursor(Qt.PointingHandCursor)
        left_button.setEnabled(not is_first)
        left_button.clicked.connect(lambda: self.move_left.emit(self.path))
        layout.addWidget(left_button)

        name = Path(path).name or path
        self.name_button = QPushButton(f"📌 {name}")
        self.name_button.setObjectName("pinChipLabel")
        self.name_button.setToolTip(path)
        self.name_button.setCursor(Qt.PointingHandCursor)
        self.name_button.clicked.connect(lambda: self.clicked.emit(self.path))
        layout.addWidget(self.name_button)

        right_button = QPushButton("▶")
        right_button.setObjectName("pinChipMove")
        right_button.setFixedSize(18, 20)
        right_button.setToolTip("Déplacer vers la droite")
        right_button.setCursor(Qt.PointingHandCursor)
        right_button.setEnabled(not is_last)
        right_button.clicked.connect(lambda: self.move_right.emit(self.path))
        layout.addWidget(right_button)

        remove_button = QPushButton("✕")
        remove_button.setObjectName("pinChipRemove")
        remove_button.setFixedSize(20, 20)
        remove_button.setToolTip("Retirer ce dossier des épingles")
        remove_button.setCursor(Qt.PointingHandCursor)
        remove_button.clicked.connect(lambda: self.unpinned.emit(self.path))
        layout.addWidget(remove_button)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rec Size Helper")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.folder: Path | None = None
        self.recordings: list[Recording] = []
        self.worker: ScanWorker | None = None
        self._pending_mp4 = []
        self._pending_mkv = []
        self._current_free_bytes: int | None = None
        self._total_mkv_bytes = 0
        self._total_mp4_bytes = 0
        self._disk_total_bytes: int | None = None
        self._other_bytes = 0
        self._syncing_sliders = False
        self._locked_gap = 0
        self.pinned_folders: list[str] = settings.load_pinned_folders()
        self.theme_name = theme.detect_windows_theme()
        self.palette = theme.get_palette(self.theme_name)

        self._build_ui()
        self.refresh_pinned_row()
        self.apply_theme(self.theme_name)
        self.update_preview()
        self._update_worker: UpdateCheckWorker | None = None
        self.check_for_updates()

    # -------------------------------------------------------------- update --
    def check_for_updates(self):
        if not is_frozen():
            return
        self._update_worker = UpdateCheckWorker()
        self._update_worker.found.connect(self.on_update_found)
        self._update_worker.start()

    def on_update_found(self, info):
        dialog = UpdateDialog(info, parent=self)
        dialog.exec()

    # ---------------------------------------------------------------- UI --
    def _build_ui(self):
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        outer_scroll.setFrameShape(QFrame.NoFrame)
        outer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(outer_scroll)

        central = QWidget()
        outer_scroll.setWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("🎬  Rec Size Helper")
        title.setObjectName("title")
        subtitle = QLabel("Visualisez et nettoyez vos enregistrements MKV / MP4 en toute sécurité")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("iconButton")
        self.theme_button.setFixedSize(34, 34)
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setToolTip("Basculer entre thème clair et thème sombre")
        self.theme_button.clicked.connect(self.toggle_theme)
        header.addWidget(self.theme_button)

        self.folder_button = QPushButton("📁  Choisir un dossier…")
        self.folder_button.setObjectName("pathButton")
        self.folder_button.clicked.connect(self.choose_folder)
        header.addWidget(self.folder_button)
        root.addLayout(header)

        self.pinned_scroll = QScrollArea()
        self.pinned_scroll.setWidgetResizable(True)
        self.pinned_scroll.setFixedHeight(42)
        self.pinned_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pinned_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pinned_scroll.setFrameShape(QFrame.NoFrame)
        self.pinned_scroll.setObjectName("pinnedScroll")
        self.pinned_container = QWidget()
        self.pinned_layout = QHBoxLayout(self.pinned_container)
        self.pinned_layout.setContentsMargins(0, 0, 0, 0)
        self.pinned_layout.setSpacing(8)
        self.pinned_scroll.setWidget(self.pinned_container)
        root.addWidget(self.pinned_scroll)

        folder_row = QHBoxLayout()
        self.folder_label = QLabel("Aucun dossier sélectionné")
        self.folder_label.setObjectName("mutedText")
        folder_row.addWidget(self.folder_label, stretch=1)

        self.pin_button = QPushButton("📌  Épingler")
        self.pin_button.setObjectName("pinToggle")
        self.pin_button.setCheckable(True)
        self.pin_button.setEnabled(False)
        self.pin_button.setCursor(Qt.PointingHandCursor)
        self.pin_button.clicked.connect(self.toggle_pin)
        folder_row.addWidget(self.pin_button)
        root.addLayout(folder_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        storage_frame = QFrame()
        storage_frame.setObjectName("card")
        storage_layout = QVBoxLayout(storage_frame)
        storage_layout.setContentsMargins(20, 16, 20, 16)
        storage_layout.setSpacing(10)

        storage_header = QHBoxLayout()
        storage_title_box = QVBoxLayout()
        storage_title_box.setSpacing(2)
        storage_title = QLabel("💾  Stockage du disque")
        storage_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        self.storage_subtitle = QLabel("Sélectionnez un dossier")
        self.storage_subtitle.setObjectName("mutedText")
        self.storage_subtitle.setStyleSheet("font-size: 12px;")
        storage_title_box.addWidget(storage_title)
        storage_title_box.addWidget(self.storage_subtitle)
        storage_header.addLayout(storage_title_box)
        storage_header.addStretch()
        self.storage_free_label = QLabel("—")
        self.storage_free_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        storage_header.addWidget(self.storage_free_label)
        storage_layout.addLayout(storage_header)

        self.storage_bar = StorageBar()
        storage_layout.addWidget(self.storage_bar)

        storage_legend = QHBoxLayout()
        storage_legend.setSpacing(18)
        storage_legend.addWidget(_legend_dot(MKV_COLOR, "MKV"))
        storage_legend.addWidget(_legend_dot(MP4_COLOR, "MP4"))
        storage_legend.addWidget(_legend_dot(OTHER_COLOR, "Autres fichiers"))
        storage_legend.addWidget(_legend_dot(FREE_COLOR, "Libre"))
        storage_legend.addStretch()
        self.recordings_count_label = QLabel("🗂️  0 enregistrements")
        self.recordings_count_label.setStyleSheet(f"color: {OTHER_COLOR}; font-size: 12px; font-weight: 700;")
        storage_legend.addWidget(self.recordings_count_label)
        storage_layout.addLayout(storage_legend)

        root.addWidget(storage_frame)

        timeline_frame = QFrame()
        timeline_frame.setObjectName("card")
        tl_layout = QVBoxLayout(timeline_frame)
        tl_layout.setContentsMargins(18, 14, 18, 14)
        tl_layout.setSpacing(10)

        self.timeline = TimelineWidget()
        tl_layout.addWidget(self.timeline)
        root.addWidget(timeline_frame, stretch=1)

        sliders_frame = QFrame()
        sliders_frame.setObjectName("card")
        sl_layout = QVBoxLayout(sliders_frame)
        sl_layout.setContentsMargins(20, 18, 20, 18)
        sl_layout.setSpacing(6)

        self.delete_label = QLabel("Sélectionnez d'abord un dossier")
        self.delete_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        self.delete_slider = QSlider(Qt.Horizontal)
        self.delete_slider.setObjectName("deleteSlider")
        self.delete_slider.setRange(0, 1000)
        self.delete_slider.setValue(0)
        self.delete_slider.valueChanged.connect(self.on_delete_slider_changed)
        sl_layout.addWidget(self.delete_label)
        sl_layout.addWidget(self.delete_slider)
        sl_layout.addSpacing(10)

        self.buffer_label = QLabel("Marge MKV")
        self.buffer_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        sl_layout.addWidget(self.buffer_label)

        mkv_slider_row = QHBoxLayout()
        mkv_slider_row.setSpacing(10)
        self.mkv_slider = QSlider(Qt.Horizontal)
        self.mkv_slider.setObjectName("bufferSlider")
        self.mkv_slider.setRange(0, 1000)
        self.mkv_slider.setValue(0)
        self.mkv_slider.valueChanged.connect(self.on_mkv_slider_changed)
        mkv_slider_row.addWidget(self.mkv_slider, stretch=1)

        self.lock_button = QPushButton("🔓")
        self.lock_button.setObjectName("lockToggle")
        self.lock_button.setCheckable(True)
        self.lock_button.setFixedSize(30, 30)
        self.lock_button.setCursor(Qt.PointingHandCursor)
        self.lock_button.setToolTip("Verrouiller l'écart entre les deux curseurs")
        self.lock_button.toggled.connect(self.toggle_lock)
        mkv_slider_row.addWidget(self.lock_button)
        sl_layout.addLayout(mkv_slider_row)

        root.addWidget(sliders_frame)

        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("summaryCard")
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(20, 14, 20, 14)
        summary_layout.setSpacing(14)

        summary_icon = QLabel("🗑️")
        summary_icon.setStyleSheet("font-size: 30px;")
        summary_layout.addWidget(summary_icon)

        self.summary_label = QLabel("")
        self.summary_label.setObjectName("summaryText")
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label, stretch=1)
        root.addWidget(self.summary_frame)

        action_row = QHBoxLayout()
        action_row.addStretch()

        self.delete_button = QPushButton("Supprimer définitivement")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.do_delete)
        action_row.addWidget(self.delete_button)

        root.addLayout(action_row)

    # ------------------------------------------------------ pinned folders --
    def refresh_pinned_row(self):
        while self.pinned_layout.count():
            item = self.pinned_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.pinned_folders:
            placeholder = QLabel("📌 Épingle un dossier pour le retrouver ici en un clic")
            placeholder.setObjectName("dimText")
            self.pinned_layout.addWidget(placeholder)
        else:
            last_idx = len(self.pinned_folders) - 1
            for idx, path in enumerate(self.pinned_folders):
                chip = PinnedChip(path, is_first=(idx == 0), is_last=(idx == last_idx))
                chip.clicked.connect(self.select_pinned_folder)
                chip.unpinned.connect(self.unpin_folder)
                chip.move_left.connect(lambda p: self.move_pin(p, -1))
                chip.move_right.connect(lambda p: self.move_pin(p, 1))
                self.pinned_layout.addWidget(chip)
        self.pinned_layout.addStretch()

    def move_pin(self, path: str, direction: int):
        try:
            idx = self.pinned_folders.index(path)
        except ValueError:
            return
        new_idx = idx + direction
        if 0 <= new_idx < len(self.pinned_folders):
            self.pinned_folders[idx], self.pinned_folders[new_idx] = (
                self.pinned_folders[new_idx],
                self.pinned_folders[idx],
            )
            settings.save_pinned_folders(self.pinned_folders)
            self.refresh_pinned_row()

    def toggle_pin(self):
        if not self.folder:
            return
        path = str(self.folder)
        if path in self.pinned_folders:
            self.pinned_folders.remove(path)
        else:
            self.pinned_folders.append(path)
        settings.save_pinned_folders(self.pinned_folders)
        self.refresh_pinned_row()
        self.update_pin_button_state()

    def unpin_folder(self, path: str):
        if path in self.pinned_folders:
            self.pinned_folders.remove(path)
            settings.save_pinned_folders(self.pinned_folders)
            self.refresh_pinned_row()
            self.update_pin_button_state()

    def update_pin_button_state(self):
        is_pinned = bool(self.folder) and str(self.folder) in self.pinned_folders
        self.pin_button.setChecked(is_pinned)
        self.pin_button.setText("📌  Épinglé" if is_pinned else "📌  Épingler")
        self.pin_button.setEnabled(bool(self.folder))

    def select_pinned_folder(self, path: str):
        folder = Path(path)
        if not folder.exists():
            QMessageBox.warning(self, "Dossier introuvable", f"Ce dossier n'existe plus :\n{path}")
            return
        self.folder = folder
        self.folder_label.setText(str(self.folder))
        self.update_pin_button_state()
        self.start_scan()

    # ---------------------------------------------------------- scanning --
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier des enregistrements")
        if not folder:
            return
        self.folder = Path(folder)
        self.folder_label.setText(str(self.folder))
        self.update_pin_button_state()
        self.start_scan()

    def start_scan(self):
        if self.worker and self.worker.isRunning():
            return
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.progress.setFormat("Analyse en cours…")
        self.folder_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.worker = ScanWorker(self.folder)
        self.worker.progress.connect(self.on_scan_progress)
        self.worker.finished_scan.connect(self.on_scan_finished)
        self.worker.error.connect(self.on_scan_error)
        self.worker.start()

    def on_scan_progress(self, done: int, total: int, name: str):
        if total:
            self.progress.setRange(0, total)
            self.progress.setValue(done)
            self.progress.setFormat(f"Analyse… {done}/{total} — {name}")

    def on_scan_finished(self, recordings: list[Recording]):
        self.recordings = recordings
        self.progress.setVisible(False)
        self.folder_button.setEnabled(True)
        self.refresh_stats()
        self.timeline.set_recordings(self.recordings)
        self.update_preview()

    def on_scan_error(self, message: str):
        self.progress.setVisible(False)
        self.folder_button.setEnabled(True)
        QMessageBox.critical(self, "Erreur", f"Impossible d'analyser le dossier :\n{message}")

    def refresh_stats(self):
        self._total_mkv_bytes = sum(r.mkv.size for r in self.recordings if r.mkv)
        self._total_mp4_bytes = sum(r.mp4.size for r in self.recordings if r.mp4)
        self.recordings_count_label.setText(f"🗂️  {len(self.recordings)} enregistrements")

        self._current_free_bytes = None
        self._disk_total_bytes = None
        self._other_bytes = 0
        if not self.folder:
            self.storage_bar.set_data([], 1)
            self.storage_subtitle.setText("Sélectionnez un dossier")
            self.storage_free_label.setText("—")
            return

        try:
            usage = shutil.disk_usage(self.folder)
        except OSError:
            self.storage_bar.set_data([], 1)
            self.storage_subtitle.setText("Impossible de lire l'espace disque")
            self.storage_free_label.setText("—")
            return

        self._current_free_bytes = usage.free
        self._disk_total_bytes = usage.total
        self._other_bytes = max(usage.total - usage.free - self._total_mkv_bytes - self._total_mp4_bytes, 0)
        self._update_storage_visual(0, 0)

    def _update_storage_visual(self, mkv_freed: int, mp4_freed: int):
        """Redraws the top storage bar — with a live preview of pending deletions if any."""
        if self._disk_total_bytes is None:
            return

        mkv_remaining = max(self._total_mkv_bytes - mkv_freed, 0)
        mp4_remaining = max(self._total_mp4_bytes - mp4_freed, 0)
        freed = mkv_freed + mp4_freed
        free_projected = self._current_free_bytes + freed

        self.storage_bar.set_data(
            [
                (mkv_remaining, QColor(MKV_COLOR)),
                (mp4_remaining, QColor(MP4_COLOR)),
                (self._other_bytes, QColor(OTHER_COLOR)),
                (free_projected, QColor(FREE_COLOR)),
            ],
            self._disk_total_bytes,
        )

        if freed > 0:
            self.storage_subtitle.setText(
                f"Aperçu après suppression — {format_size(self._disk_total_bytes - free_projected)} "
                f"sur {format_size(self._disk_total_bytes)} utilisés"
            )
            self.storage_free_label.setText(f"{format_size(free_projected)} libres (aperçu)")
        else:
            self.storage_subtitle.setText(
                f"{format_size(self._disk_total_bytes - self._current_free_bytes)} sur "
                f"{format_size(self._disk_total_bytes)} utilisés "
                f"— dont {format_size(self._total_mkv_bytes + self._total_mp4_bytes)} d'enregistrements"
            )
            self.storage_free_label.setText(f"{format_size(self._current_free_bytes)} libres")

    # ------------------------------------------------------- slider logic --
    def on_delete_slider_changed(self):
        if not self._syncing_sliders:
            self._syncing_sliders = True
            try:
                if self.lock_button.isChecked():
                    target = max(0, min(self.delete_slider.value() - self._locked_gap, self.mkv_slider.maximum()))
                    self.mkv_slider.setValue(target)
                elif self.mkv_slider.value() > self.delete_slider.value():
                    self.mkv_slider.setValue(self.delete_slider.value())
            finally:
                self._syncing_sliders = False
        self.update_preview()

    def on_mkv_slider_changed(self):
        if not self._syncing_sliders:
            self._syncing_sliders = True
            try:
                if self.lock_button.isChecked():
                    target = max(0, min(self.mkv_slider.value() + self._locked_gap, self.delete_slider.maximum()))
                    self.delete_slider.setValue(target)
                elif self.mkv_slider.value() > self.delete_slider.value():
                    self.mkv_slider.setValue(self.delete_slider.value())
                    return
            finally:
                self._syncing_sliders = False
        self.update_preview()

    def toggle_lock(self, checked: bool):
        if checked:
            self._locked_gap = self.delete_slider.value() - self.mkv_slider.value()
        self.lock_button.setText("🔒" if checked else "🔓")

    def compute_cutoffs(self):
        now = datetime.now()
        oldest = min(r.date for r in self.recordings)
        max_age_days = max(math.ceil((now - oldest).total_seconds() / 86400), 1)

        mp4_percent = self.delete_slider.value() / self.delete_slider.maximum()
        cutoff_days_mp4 = round(max_age_days * (1 - mp4_percent))

        mkv_percent = self.mkv_slider.value() / self.mkv_slider.maximum()
        cutoff_days_mkv = round(max_age_days * (1 - mkv_percent))
        cutoff_days_mkv = max(cutoff_days_mkv, cutoff_days_mp4)

        mp4_cutoff_date = now - timedelta(days=cutoff_days_mp4)
        mkv_cutoff_date = now - timedelta(days=cutoff_days_mkv)
        buffer_days = cutoff_days_mkv - cutoff_days_mp4
        return mp4_cutoff_date, mkv_cutoff_date, cutoff_days_mp4, cutoff_days_mkv, buffer_days

    def update_preview(self):
        if not self.recordings:
            self.delete_label.setText("🗑️  Sélectionnez d'abord un dossier")
            self.buffer_label.setText("🛡️  Marge MKV")
            self.summary_label.setText("Sélectionnez un dossier pour voir ce qui serait supprimé.")
            self.delete_button.setEnabled(False)
            self.timeline.set_cutoffs(None, None)
            self._update_storage_visual(0, 0)
            return

        mp4_cutoff, mkv_cutoff, cutoff_days_mp4, cutoff_days_mkv, buffer_days = self.compute_cutoffs()
        self.timeline.set_cutoffs(mp4_cutoff, mkv_cutoff)

        self.delete_label.setText(
            f"🗑️  {cutoff_days_mp4} jours (avant le {mp4_cutoff.strftime('%d/%m/%Y')})"
        )
        self.buffer_label.setText(f"🛡️  Marge MKV de {buffer_days} jours")

        mp4_to_delete = [r.mp4 for r in self.recordings if r.mp4 and r.age_days >= cutoff_days_mp4]
        mkv_to_delete = [r.mkv for r in self.recordings if r.mkv and r.age_days >= cutoff_days_mkv]
        total_freed = sum(f.size for f in mp4_to_delete) + sum(f.size for f in mkv_to_delete)

        self._pending_mp4 = mp4_to_delete
        self._pending_mkv = mkv_to_delete

        mkv_freed_bytes = sum(f.size for f in mkv_to_delete)
        mp4_freed_bytes = sum(f.size for f in mp4_to_delete)
        self._update_storage_visual(mkv_freed_bytes, mp4_freed_bytes)

        main_line = (
            f"{len(mp4_to_delete)} MP4 + {len(mkv_to_delete)} MKV seront supprimés définitivement "
            f"— {format_size(total_freed)} libérés"
        )
        summary_html = f"<div>{main_line}</div>"
        if self._current_free_bytes is not None:
            projected_free = self._current_free_bytes + total_freed
            summary_html += (
                f"<div style='font-size:13px; font-weight:500; color:{self.palette['summary_sub']}; margin-top:5px;'>"
                f"💽 Espace libre après suppression : ~{format_size(projected_free)} "
                f"(contre {format_size(self._current_free_bytes)} actuellement)"
                "</div>"
            )
        self.summary_label.setText(summary_html)
        self.delete_button.setEnabled(bool(mp4_to_delete or mkv_to_delete))

    # --------------------------------------------------------------- theme --
    def toggle_theme(self):
        self.apply_theme("light" if self.theme_name == "dark" else "dark")

    def apply_theme(self, name: str):
        self.theme_name = name
        self.palette = theme.get_palette(name)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.palette))
        self.theme_button.setText("☀" if name == "dark" else "☾")
        self.timeline.set_theme(self.palette)
        self.storage_bar.set_theme(self.palette)
        if self.recordings or self.folder:
            self.update_preview()

    # ------------------------------------------------------------ delete --
    def do_delete(self):
        mp4_files = list(self._pending_mp4)
        mkv_files = list(self._pending_mkv)
        if not mp4_files and not mkv_files:
            return

        total_freed = sum(f.size for f in mp4_files) + sum(f.size for f in mkv_files)
        msg = (
            f"{len(mp4_files)} fichier(s) MP4 et {len(mkv_files)} fichier(s) MKV "
            f"({format_size(total_freed)}) vont être supprimés DÉFINITIVEMENT de votre disque.\n\n"
            "⚠️ Ils ne passeront PAS par la Corbeille — cette action est irréversible.\n\n"
            "Continuer ?"
        )
        reply = QMessageBox.warning(
            self, "Confirmer la suppression définitive", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        failed: list[tuple[Path, str]] = []
        deleted_paths: set[Path] = set()
        for f in mp4_files + mkv_files:
            try:
                f.path.unlink()
                deleted_paths.add(f.path)
            except OSError as e:
                failed.append((f.path, str(e)))

        self._remove_deleted_from_model(deleted_paths)
        self.refresh_stats()
        self.timeline.set_recordings(self.recordings)
        self.update_preview()

        if failed:
            details = "\n".join(f"- {p.name} : {err}" for p, err in failed[:10])
            QMessageBox.warning(
                self, "Certains fichiers n'ont pas pu être supprimés",
                f"{len(failed)} fichier(s) ont échoué :\n{details}",
            )
        else:
            QMessageBox.information(
                self, "Terminé",
                f"{format_size(total_freed)} supprimés définitivement et libérés sur le disque.",
            )

    def _remove_deleted_from_model(self, deleted_paths: set[Path]):
        new_recordings = []
        for r in self.recordings:
            if r.mkv and r.mkv.path in deleted_paths:
                r.mkv = None
            if r.mp4 and r.mp4.path in deleted_paths:
                r.mp4 = None
            if r.mkv or r.mp4:
                new_recordings.append(r)
        self.recordings = new_recordings
