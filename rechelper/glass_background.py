from __future__ import annotations

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .theme import DARK


class GlassBackground(QWidget):
    """Fond des fenêtres : un aplat uni, gris très clair ou violet nuit selon le thème. Les
    panneaux pleins posés dessus portent seuls le contraste — plus de taches de couleur.
    (Le nom date de l'ancien design en verre dépoli ; il est gardé pour ne pas toucher aux
    imports.)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = DARK

    def set_theme(self, palette: dict):
        self._palette = palette
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._palette["bg"]))
        painter.end()
