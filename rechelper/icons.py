"""Icônes au trait (style Feather : trait 1.8, bouts et angles arrondis), dessinées à la main
en SVG et rendues dans la couleur du thème — reprises de Youtube Scrapper.

Elles remplacent tous les emoji de l'interface : c'est l'esthétique plate et nette de l'icône
de l'appli, et un emoji affiché force le chargement de la police couleur Segoe UI Emoji
(~1 s au démarrage). Seuls restent les emoji que l'utilisateur choisit pour ses dossiers
épinglés.

Les icônes posées sur des widgets durables sont « liées » (bind) : un changement de thème
les redessine dans les nouvelles couleurs. Les panneaux, recréés à chaque ouverture,
prennent simplement les couleurs du moment.
"""

from __future__ import annotations

import math
import weakref

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap

_STROKE = 1.8


def _gear() -> str:
    teeth, r_out, r_in = 8, 9.4, 7.0
    width = math.pi / teeth * 0.52
    points = []
    for i in range(teeth):
        angle = 2 * math.pi * i / teeth
        for radius, offset in ((r_in, -width), (r_out, -width * 0.62), (r_out, width * 0.62), (r_in, width)):
            points.append((12 + radius * math.cos(angle + offset), 12 + radius * math.sin(angle + offset)))
    path = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in points) + " Z"
    return f'<path d="{path}"/><circle cx="12" cy="12" r="3"/>'


def _sun() -> str:
    rays = []
    for i in range(8):
        angle = math.pi / 4 * i
        x1, y1 = 12 + 6.8 * math.cos(angle), 12 + 6.8 * math.sin(angle)
        x2, y2 = 12 + 9.2 * math.cos(angle), 12 + 9.2 * math.sin(angle)
        rays.append(f"M{x1:.2f} {y1:.2f} L{x2:.2f} {y2:.2f}")
    return f'<circle cx="12" cy="12" r="4"/><path d="{" ".join(rays)}"/>'


_SHIELD = '<path d="M12 3l7.5 3v5.6c0 4.4-3.1 8.2-7.5 9.4-4.4-1.2-7.5-5-7.5-9.4V6z"/>'
_LOCK_BODY = '<rect x="5" y="11" width="14" height="10" rx="2.2"/>'

SHAPES = {
    "settings": _gear(),
    "sun": _sun(),
    "moon": '<path d="M20 14.6A8.2 8.2 0 0 1 9.4 4 8.2 8.2 0 1 0 20 14.6z"/>',
    "x": '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    "check": '<path d="M5 12.6l4.4 4.4L19 7.4"/>',
    "folder": '<path d="M3.5 7a2 2 0 0 1 2-2h4l2 2.4h7a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
    "pin": '<path d="M12 16.5v5"/><path d="M8.6 3.5h6.8l-1 6.1 3.1 3.6v1.3H6.5v-1.3l3.1-3.6z"/>',
    "trash": '<path d="M4.5 7h15"/><path d="M9.5 7V4.5h5V7"/>'
    '<path d="M6.5 7l.9 12.2A1.8 1.8 0 0 0 9.2 21h5.6a1.8 1.8 0 0 0 1.8-1.8L17.5 7"/>',
    "shield_check": _SHIELD + '<path d="M8.8 12.2l2.3 2.3 4.3-4.6"/>',
    "lock": _LOCK_BODY + '<path d="M8 11V7.6a4 4 0 0 1 8 0V11"/>',
    "unlock": _LOCK_BODY + '<path d="M8 11V7.6a4 4 0 0 1 7.7-1.6"/>',
    "drive": '<path d="M3 13.5h18"/>'
    '<path d="M6.2 5.6L3 13.5v4.5a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4.5l-3.2-7.9A2 2 0 0 0 15.9 4.4H8.1a2 2 0 0 0-1.9 1.2z"/>'
    '<path d="M7 16.8h.01M10.5 16.8h.01"/>',
    "chevron_left": '<path d="M14.5 18l-6-6 6-6"/>',
    "chevron_right": '<path d="M9.5 18l6-6-6-6"/>',
    "more": '<circle cx="5.6" cy="12" r="1.1"/><circle cx="12" cy="12" r="1.1"/><circle cx="18.4" cy="12" r="1.1"/>',
    "download": '<path d="M12 4v11"/><path d="M7.5 10.5L12 15l4.5-4.5"/><path d="M4.5 19.5h15"/>',
    "error": '<circle cx="12" cy="12" r="8.8"/><path d="M15 9l-6 6M9 9l6 6"/>',
}

# couleur nommée -> clé de palette
_ROLES = {
    "text": "text",
    "text2": "text2",
    "muted": "text_muted",
    "dim": "text_dim",
    "accent": "accent",
    "success": "success",
    "warn": "warn",
}

_palette: dict = {}
_cache: dict = {}
_bindings: list = []
_chips: list = []


def set_palette(palette: dict):
    """Change le thème des icônes et redessine toutes les icônes liées encore vivantes."""
    global _palette
    _palette = palette
    _cache.clear()
    alive = []
    for ref, args in _bindings:
        widget = ref()
        if widget is None:
            continue
        try:
            widget.setIcon(icon(*args))
        except RuntimeError:  # widget C++ déjà détruit
            continue
        alive.append((ref, args))
    _bindings[:] = alive

    chips = []
    for ref, args in _chips:
        label = ref()
        if label is None:
            continue
        try:
            _paint_chip(label, *args)
        except RuntimeError:
            continue
        chips.append((ref, args))
    _chips[:] = chips


def color(role: str) -> str:
    if role.startswith("#"):
        return role
    if role == "white":
        return "#ffffff"
    if role in _ROLES:
        return _palette.get(_ROLES[role], "#888888")
    if role in _palette and isinstance(_palette[role], tuple):  # famille : couleur du trait
        return _palette[role][1]
    return _palette.get(role, "#888888")


def pixmap(name: str, role: str = "text", size: int = 18, ratio: float = 2.0) -> QPixmap:
    key = (name, color(role), size, ratio)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    from PySide6.QtSvg import QSvgRenderer

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color(role)}" stroke-width="{_STROKE}" stroke-linecap="round" '
        f'stroke-linejoin="round">{SHAPES[name]}</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    side = round(size * ratio)
    image = QPixmap(side, side)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    image.setDevicePixelRatio(ratio)
    _cache[key] = image
    return image


def icon(
    name: str,
    role: str = "text",
    size: int = 18,
    checked_role: str | None = None,
    checked_name: str | None = None,
) -> QIcon:
    """QIcon avec un état désactivé estompé et, pour les boutons cochables, une couleur —
    voire une forme (cadenas ouvert / fermé) — différente quand le bouton est coché."""
    on_name = checked_name or name
    result = QIcon()
    result.addPixmap(pixmap(name, role, size), QIcon.Normal, QIcon.Off)
    result.addPixmap(pixmap(on_name, checked_role or role, size), QIcon.Normal, QIcon.On)
    result.addPixmap(pixmap(name, "dim", size), QIcon.Disabled, QIcon.Off)
    result.addPixmap(pixmap(on_name, "dim", size), QIcon.Disabled, QIcon.On)
    return result


def bind(
    widget,
    name: str,
    role: str = "text",
    size: int = 18,
    checked_role: str | None = None,
    checked_name: str | None = None,
):
    """Pose l'icône et la retient pour la redessiner au prochain changement de thème."""
    args = (name, role, size, checked_role, checked_name)
    widget.setIcon(icon(*args))
    widget.setIconSize(QSize(size, size))
    _bindings.append((weakref.ref(widget), args))


def chip_style(family: str, radius: int = 8) -> str:
    background, _ = _palette[family]
    return f"background-color: {background}; border-radius: {radius}px;"


def _paint_chip(label, name: str, family: str, icon_size: int, radius: int):
    label.setPixmap(pixmap(name, family, icon_size))
    label.setStyleSheet(chip_style(family, radius))


def make_chip(name: str, family: str, size: int = 28, icon_size: int | None = None, radius: int | None = None):
    """Pastille teintée par famille portant une icône — en-têtes de cartes et de panneaux.
    Retenue comme les icônes liées : un changement de thème la repeint."""
    from PySide6.QtWidgets import QLabel

    label = QLabel()
    label.setFixedSize(size, size)
    label.setAlignment(Qt.AlignCenter)
    args = (name, family, icon_size or round(size * 0.58), radius if radius is not None else round(size * 0.27))
    _paint_chip(label, *args)
    _chips.append((weakref.ref(label), args))
    return label
