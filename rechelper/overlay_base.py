from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

_BLUR_RADIUS = 16


def backdrop_color(palette: dict) -> QColor:
    # Dark theme's own UI is already near-black — a heavy black dim on top
    # of it crushes the blurred content to unreadable black, so it gets a
    # much lighter touch than light theme needs.
    if palette.get("name") == "dark":
        return QColor(30, 24, 48, 70)
    return QColor(8, 6, 18, 150)


class ModalOverlay(QWidget):
    """Base for in-window modal panels: blurs+dims the app behind a
    centered card instead of opening a separate OS window. One-shot —
    construct fresh each time you need one, it self-deletes on close."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self._main_window = main_window
        self.setFocusPolicy(Qt.StrongFocus)
        self._backdrop_color = backdrop_color(getattr(main_window, "palette", {}) or {})
        self.hide()

        outer = QVBoxLayout(self)
        outer.addStretch()
        self._center_row = QHBoxLayout()
        self._center_row.addStretch()
        outer.addLayout(self._center_row)
        outer.addStretch()

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(self._on_anim_finished)

    def set_card(self, card: QWidget):
        self._center_row.addWidget(card)
        self._center_row.addStretch()

    def set_theme(self, palette: dict):
        self._backdrop_color = backdrop_color(palette)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._backdrop_color)
        super().paintEvent(event)

    def mousePressEvent(self, event):
        # only reaches here for genuine backdrop clicks — clicks on the
        # card are consumed by its own child widgets first
        self.close_overlay()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_overlay()
        else:
            super().keyPressEvent(event)

    def open_over(self):
        self.set_theme(self._main_window.palette)
        self.setGeometry(self._main_window.rect())

        host = self._main_window.centralWidget()
        blur = QGraphicsBlurEffect(host)
        blur.setBlurRadius(_BLUR_RADIUS)
        host.setGraphicsEffect(blur)

        self.show()
        self.raise_()
        self.setFocus()
        self._anim.stop()
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(1.0)
        self._anim.start()

    def close_overlay(self):
        self._anim.stop()
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _on_anim_finished(self):
        if self._opacity_effect.opacity() <= 0.01:
            self.hide()
            self._main_window.centralWidget().setGraphicsEffect(None)
            self.deleteLater()
