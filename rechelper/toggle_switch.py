from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton, QWidget

from . import icons

_FRAME_MARGIN = 3
# Les paires d'icônes n'ont pas les mêmes proportions : à laisser chaque bouton se
# dimensionner tout seul, les deux moitiés finissent de largeurs différentes et le
# surlignage qui glisse tombe à côté. Une taille fixe les garde identiques.
_BUTTON_SIZE = QSize(42, 30)


class ToggleSwitch(QWidget):
    """Interrupteur à deux icônes (clair/sombre, ouvert/verrouillé) — un choix explicite
    plutôt qu'un bouton bascule muet, avec le segment actif qui glisse d'un côté à l'autre."""

    toggled = Signal(bool)

    def __init__(self, icon_off: str = "sun", icon_on: str = "moon", parent=None):
        super().__init__(parent)
        self._checked = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._frame = QFrame()
        self._frame.setObjectName("segmentIconPill")
        frame_layout = QHBoxLayout(self._frame)
        frame_layout.setContentsMargins(_FRAME_MARGIN, _FRAME_MARGIN, _FRAME_MARGIN, _FRAME_MARGIN)
        frame_layout.setSpacing(0)

        # Créé avant les boutons pour rester derrière eux dans l'ordre de peinture.
        self._thumb = QFrame(self._frame)
        self._thumb.setObjectName("segmentIconThumb")
        self._thumb.lower()

        self.off_button = QPushButton()
        self.on_button = QPushButton()
        # côté « non » : simplement noirci quand il est choisi ; côté « oui » : en accent
        icons.bind(self.off_button, icon_off, "dim", 16, checked_role="text")
        icons.bind(self.on_button, icon_on, "dim", 16, checked_role="accent")
        for button in (self.off_button, self.on_button):
            button.setObjectName("segmentIconItem")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedSize(_BUTTON_SIZE)
            frame_layout.addWidget(button)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.addButton(self.off_button)
        self._group.addButton(self.on_button)

        self.off_button.clicked.connect(lambda: self._set_checked(False))
        self.on_button.clicked.connect(lambda: self._set_checked(True))

        self._anim = QPropertyAnimation(self._thumb, b"geometry", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self.off_button.setChecked(True)
        outer.addWidget(self._frame)
        # Taille figée : dans une ligne plus haute que lui (description sur deux lignes),
        # le rail s'étirait sur toute la hauteur au lieu de rester une pastille.
        self.setFixedSize(
            _BUTTON_SIZE.width() * 2 + _FRAME_MARGIN * 2, _BUTTON_SIZE.height() + _FRAME_MARGIN * 2
        )
        self._sync_thumb(animate=False)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self._set_checked(checked, emit=False)

    def set_theme(self, palette: dict):
        # couleurs : feuille de style globale et icônes liées (icons.set_palette)
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_thumb(animate=False)

    def _target_rect(self, checked: bool) -> QRect:
        x = _FRAME_MARGIN + (_BUTTON_SIZE.width() if checked else 0)
        return QRect(x, _FRAME_MARGIN, _BUTTON_SIZE.width(), _BUTTON_SIZE.height())

    def _sync_thumb(self, animate: bool):
        target = self._target_rect(self._checked)
        self._anim.stop()
        if not animate:
            self._thumb.setGeometry(target)
            return
        self._anim.setStartValue(self._thumb.geometry())
        self._anim.setEndValue(target)
        self._anim.start()

    def _set_checked(self, checked: bool, emit: bool = True):
        changed = checked != self._checked
        self._checked = checked
        self.on_button.setChecked(checked)
        self.off_button.setChecked(not checked)
        self._sync_thumb(animate=True)
        if emit and changed:
            self.toggled.emit(checked)
