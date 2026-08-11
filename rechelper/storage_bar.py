from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QRectF, QVariantAnimation
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from .theme import DARK, qcolor


class StorageBar(QWidget):
    """A liquid-glass segmented storage pill. Segment sizes animate smoothly
    toward their new values instead of snapping, so slider drags feel fluid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        self._colors: list[QColor] = []
        self._display: list[float] = []
        self._start_vals: list[float] = []
        self._targets: list[float] = []
        self._total_capacity = 1.0
        self._palette = DARK

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(340)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.valueChanged.connect(self._on_tick)

    def set_theme(self, palette: dict):
        self._palette = palette
        self.update()

    def set_data(self, segments: list[tuple[float, QColor]], total_capacity: float):
        self._total_capacity = max(total_capacity, 1.0)
        values = [float(v) for v, _c in segments]
        self._colors = [c for _v, c in segments]

        if len(self._display) == len(values) and values:
            self._start_vals = list(self._display)
            self._targets = values
            self._anim.stop()
            self._anim.start()
        else:
            self._display = list(values)
            self._targets = list(values)
            self.update()

    def _on_tick(self, t):
        t = float(t)
        self._display = [s + (e - s) * t for s, e in zip(self._start_vals, self._targets)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)
        painter.fillRect(rect, qcolor(self._palette["storage_track_bg"]))

        x = 0.0
        boundaries: list[float] = []
        for value, color in zip(self._display, self._colors):
            w = rect.width() * (value / self._total_capacity)
            if w <= 0:
                continue
            seg_rect = QRectF(x, 0, w, rect.height())
            gradient = QLinearGradient(seg_rect.topLeft(), seg_rect.bottomLeft())
            top = QColor(color).lighter(115)
            top.setAlpha(235)
            bottom = QColor(color)
            bottom.setAlpha(235)
            gradient.setColorAt(0.0, top)
            gradient.setColorAt(1.0, bottom)
            painter.fillRect(seg_rect, gradient)
            x += w
            boundaries.append(x)

        # glossy top sheen across the whole pill — the "liquid glass" touch
        gloss = QLinearGradient(0, 0, 0, rect.height() * 0.55)
        gloss.setColorAt(0.0, QColor(255, 255, 255, 100))
        gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(QRectF(0, 0, rect.width(), rect.height() * 0.55), gloss)

        painter.setClipping(False)
        gap_color = qcolor(self._palette["storage_gap"])
        for bx in boundaries[:-1]:
            painter.fillRect(QRectF(bx - 1, 0, 2, rect.height()), gap_color)

        painter.end()
