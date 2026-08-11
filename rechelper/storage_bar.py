from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from .theme import DARK


class StorageBar(QWidget):
    """An iOS-Settings-style rounded, segmented storage usage bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self._segments: list[tuple[float, QColor]] = []
        self._total_capacity = 1.0
        self._palette = DARK

    def set_theme(self, palette: dict):
        self._palette = palette
        self.update()

    def set_data(self, segments: list[tuple[float, QColor]], total_capacity: float):
        self._segments = segments
        self._total_capacity = max(total_capacity, 1.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)
        painter.fillRect(rect, QColor(self._palette["storage_track_bg"]))

        x = 0.0
        boundaries: list[float] = []
        for value, color in self._segments:
            w = rect.width() * (value / self._total_capacity)
            if w <= 0:
                continue
            painter.fillRect(QRectF(x, 0, w, rect.height()), color)
            x += w
            boundaries.append(x)

        painter.setClipping(False)
        gap_color = QColor(self._palette["storage_gap"])
        for bx in boundaries[:-1]:
            painter.fillRect(QRectF(bx - 1, 0, 2, rect.height()), gap_color)

        painter.end()
