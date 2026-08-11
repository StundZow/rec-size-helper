from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .scanner import scan_folder


class ScanWorker(QThread):
    progress = Signal(int, int, str)
    finished_scan = Signal(list)
    error = Signal(str)

    def __init__(self, folder: Path):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            recordings = scan_folder(
                self.folder,
                progress=lambda done, total, name: self.progress.emit(done, total, name),
            )
            self.finished_scan.emit(recordings)
        except Exception as e:  # surface any scan failure to the UI instead of crashing silently
            self.error.emit(str(e))
