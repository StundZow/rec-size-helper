from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget

from .theme import DARK


class GlassBackground(QWidget):
    """Soft pastel backdrop with a few gentle color accents in the corners.

    Radial gradients are inherently soft-edged, so the accents read as blurred
    color washes without an actual blur pass. Most of the surface stays close
    to the base tone so the frosted cards above keep their contrast.
    """

    # (rel_x, rel_y, rel_radius) — anchored near corners, radius as a fraction
    # of the larger window dimension.
    _BLOB_LAYOUT = [
        (0.03, -0.05, 0.45),
        (0.97, 0.05, 0.40),
        (0.90, 1.00, 0.50),
        (0.06, 0.95, 0.38),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = DARK

    def set_theme(self, palette: dict):
        self._palette = palette
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        base = QLinearGradient(QPointF(0, 0), QPointF(rect.width(), rect.height()))
        base.setColorAt(0.0, QColor(self._palette["bg_base"]))
        base.setColorAt(1.0, QColor(self._palette["bg_base2"]))
        painter.fillRect(rect, base)

        span = max(rect.width(), rect.height())
        alpha = self._palette["blob_alpha"]
        for (rx, ry, rr), color_hex in zip(self._BLOB_LAYOUT, self._palette["blob_colors"]):
            cx = rect.width() * rx
            cy = rect.height() * ry
            radius = span * rr

            gradient = QRadialGradient(QPointF(cx, cy), radius)
            color = QColor(color_hex)
            color.setAlpha(alpha)
            edge = QColor(color_hex)
            edge.setAlpha(0)
            gradient.setColorAt(0.0, color)
            gradient.setColorAt(1.0, edge)
            painter.fillRect(rect, gradient)

        painter.end()
