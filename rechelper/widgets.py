"""Petites briques d'interface partagées par la fenêtre, les panneaux, l'installateur et les
dialogues, pour que tous suivent la même grammaire que Youtube Scrapper : en-tête avec
pastille teintée, boutons avec icône au trait, encadré d'information."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from . import icons

_OBJECT_NAMES = {
    "primary": "updateButton",   # dégradé du logo
    "destructive": "deleteButton",  # dégradé du logo, plus grand : l'action de l'appli
    "secondary": "pathButton",
    "icon": "iconButton",
}


def button(
    text: str,
    icon_name: str | None = None,
    kind: str = "secondary",
    on_click: Callable | None = None,
    tooltip: str | None = None,
    bind: bool = False,
) -> QPushButton:
    """kind : primary / destructive (dégradé, icône blanche), secondary (contour), icon."""
    btn = QPushButton(text)
    btn.setObjectName(_OBJECT_NAMES[kind])
    btn.setCursor(Qt.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    if icon_name:
        role = {"primary": "white", "destructive": "white", "icon": "muted"}.get(kind, "accent")
        size = 18 if kind == "icon" else 16
        if bind:
            icons.bind(btn, icon_name, role, size)
        else:
            btn.setIcon(icons.icon(icon_name, role, size))
            btn.setIconSize(QSize(size, size))
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def icon_button(icon_name: str, tooltip: str, on_click: Callable | None = None, size: int = 34, bind: bool = False):
    btn = button("", icon_name, "icon", on_click, tooltip, bind=bind)
    btn.setFixedSize(size, size)
    return btn


def panel_header(
    title: str,
    subtitle: str | None = None,
    icon_name: str | None = None,
    family: str = "f_violet",
) -> QHBoxLayout:
    """En-tête de panneau ou de dialogue : pastille teintée, titre, sous-titre."""
    row = QHBoxLayout()
    row.setSpacing(12)
    if icon_name:
        row.addWidget(icons.make_chip(icon_name, family, size=38, icon_size=20, radius=10), alignment=Qt.AlignTop)

    text_box = QVBoxLayout()
    text_box.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("panelTitle")
    title_label.setWordWrap(True)
    text_box.addWidget(title_label)
    if subtitle is not None:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("mutedText")
        subtitle_label.setWordWrap(True)
        text_box.addWidget(subtitle_label)
    row.addLayout(text_box, stretch=1)
    return row


def chip_label(icon_name: str, family: str, text: str, object_name: str = "rowTitle") -> tuple[QHBoxLayout, QLabel]:
    """Pastille teintée + libellé sur une ligne (titres de carte, lignes des curseurs).
    Renvoie le libellé pour qu'on puisse en changer le texte ensuite."""
    row = QHBoxLayout()
    row.setSpacing(10)
    row.addWidget(icons.make_chip(icon_name, family, size=28, icon_size=16, radius=8))
    label = QLabel(text)
    label.setObjectName(object_name)
    row.addWidget(label, stretch=1)
    return row, label


def note(text: str) -> QFrame:
    """Encadré d'information discret, sur rail gris."""
    frame = QFrame()
    frame.setObjectName("note")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 13, 16, 13)
    label = QLabel(text)
    label.setTextFormat(Qt.RichText)
    label.setWordWrap(True)
    label.setObjectName("mutedText")
    layout.addWidget(label)
    return frame
