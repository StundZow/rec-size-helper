from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QVBoxLayout, QWidget

# La carte monte légèrement en apparaissant au lieu de surgir sur place : c'est ce
# petit décalage qui fait lire l'ouverture comme un mouvement et pas comme un flash.
_CARD_RISE = 18

# Ombre douce sous la carte, peinte à la main en couches concentriques : un effet
# QGraphicsDropShadowEffect ferait recalculer toute la carte à chaque repeinture.
_SHADOW_LAYERS = 14
_SHADOW_SPREAD = 26
_SHADOW_DROP = 10
_CARD_RADIUS = 14


def backdrop_color(palette: dict) -> QColor:
    """Voile uni sur l'appli derrière un panneau — plus de flou : l'esthétique est plate,
    c'est le contraste entre ce voile et la carte pleine qui détache le panneau."""
    return QColor(*palette.get("backdrop", (20, 16, 32, 110)))


class ModalOverlay(QWidget):
    """Base des panneaux dans la fenêtre : un voile uni sur l'appli et une carte centrée
    avec son ombre, au lieu d'une fenêtre Windows séparée. À usage unique — on en
    construit un neuf à chaque ouverture, il se détruit à la fermeture."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self._main_window = main_window
        self.setFocusPolicy(Qt.StrongFocus)
        palette = getattr(main_window, "palette", {}) or {}
        self._backdrop_color = backdrop_color(palette)
        self._shadow_rgb = palette.get("shadow", (20, 16, 32))
        self.hide()

        self._outer = QVBoxLayout(self)
        self._outer.addStretch()
        self._center_row = QHBoxLayout()
        self._center_row.addStretch()
        self._outer.addLayout(self._center_row)
        self._outer.addStretch()

        self._card: QWidget | None = None
        self._card_offset = 0

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._anim.setDuration(240)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self._card_anim = QPropertyAnimation(self, b"cardOffset", self)
        self._card_anim.setDuration(280)
        self._card_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(self._anim)
        self._group.addAnimation(self._card_anim)
        self._group.finished.connect(self._on_anim_finished)

    def set_card(self, card: QWidget):
        self._card = card
        self._center_row.addWidget(card)
        self._center_row.addStretch()

    # Décaler la carte via une marge du layout (plutôt qu'en déplaçant le widget) garde le
    # placement piloté par le layout : rien ne se remet brutalement en place si la fenêtre
    # est redimensionnée pendant l'animation.
    def get_card_offset(self) -> int:
        return self._card_offset

    def set_card_offset(self, value: int):
        self._card_offset = value
        self._outer.setContentsMargins(0, max(value, 0) * 2, 0, 0)
        # l'ombre déborde de la carte : sans repeinture complète, elle laisserait une
        # traînée en suivant la carte pendant l'animation d'ouverture
        self.update()

    cardOffset = Property(int, get_card_offset, set_card_offset)

    def set_theme(self, palette: dict):
        self._backdrop_color = backdrop_color(palette)
        self._shadow_rgb = palette.get("shadow", (20, 16, 32))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._backdrop_color)

        if self._card is not None and self._card.isVisible():
            rect = QRectF(self._card.geometry()).translated(0, _SHADOW_DROP)
            painter.setPen(Qt.NoPen)
            for i in range(_SHADOW_LAYERS):
                grow = _SHADOW_SPREAD * (1 - i / _SHADOW_LAYERS)
                alpha = round(70 * ((i + 1) / _SHADOW_LAYERS) ** 2 / _SHADOW_LAYERS * 2.2)
                path = QPainterPath()
                radius = _CARD_RADIUS + grow
                path.addRoundedRect(rect.adjusted(-grow, -grow, grow, grow), radius, radius)
                painter.setBrush(QColor(*self._shadow_rgb, min(alpha, 255)))
                painter.drawPath(path)
        painter.end()
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

        self.set_card_offset(_CARD_RISE)
        self.show()
        self.raise_()
        self.setFocus()
        self._start_animation(target_opacity=1.0, target_offset=0)

    def close_overlay(self):
        self._start_animation(target_opacity=0.0, target_offset=_CARD_RISE)

    def _start_animation(self, target_opacity: float, target_offset: int):
        self._group.stop()
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(target_opacity)
        self._card_anim.setStartValue(self._card_offset)
        self._card_anim.setEndValue(target_offset)
        self._group.start()

    def _on_anim_finished(self):
        if self._opacity_effect.opacity() <= 0.01:
            self.hide()
            self.deleteLater()
