"""Palettes clair/sombre, de la même famille que l'icône de l'appli : des surfaces unies et
neutres (fond gris très clair ou violet nuit, panneaux pleins à fine bordure), et toute la
couleur prise dans le dégradé du logo, rose #FF4F8B → violet #7B3FF2.

- les deux bouts du dégradé sont les deux séries : MKV en rose, MP4 en violet (comme la jauge
  en deux tons du logo), sur la barre de stockage, la courbe et les curseurs ;
- le dégradé lui-même remplit l'action principale (bouton Supprimer, Installer…), un peu
  assombri pour que le texte blanc reste lisible, et le logo exact au survol ;
- un accent violet uni sert à tout le reste (focus, éléments cochés, liens).

Le thème sombre est défini couleur par couleur, pas simplement inversé."""

from __future__ import annotations

import re
import winreg

from PySide6.QtGui import QColor

LOGO_PINK = "#FF4F8B"
LOGO_VIOLET = "#7B3FF2"

LIGHT = {
    "name": "light",
    # surfaces
    "bg": "#f5f4f8",
    "panel": "#ffffff",
    "soft": "#f8f7fb",
    "soft2": "#efedf4",
    "line": "#e5e2ec",
    "line2": "#d2cde0",
    "hover": "rgba(29, 26, 40, 0.055)",
    # texte
    "text": "#1d1a28",
    "text2": "#3c3650",
    "text_muted": "#6a6480",
    "text_dim": "#9690a8",
    # accent uni (violet du logo, un cran plus profond pour le texte sur blanc)
    "accent": "#6d32e6",
    "accent2": "#7b3ff2",
    "accent_bg": "#f1ebfe",
    "accent_line": "#d6c6fb",
    # dégradé de l'action principale : normal (assombri) et survol (logo exact)
    "grad_a": "#f03a7e",
    "grad_b": "#6f36e8",
    "grad_a_hover": LOGO_PINK,
    "grad_b_hover": LOGO_VIOLET,
    # barre d'avancement avec texte dessus : dégradé éclairci, texte sombre lisible
    "progress_a": "#ffb6cf",
    "progress_b": "#c9aefa",
    # séries de données
    "mkv": LOGO_PINK,
    "mp4": LOGO_VIOLET,
    "other": "#aba4bf",
    "free": "#ecebf2",
    "chart_grid": "rgba(29, 26, 40, 0.08)",
    "zone_alpha": 24,
    # états
    "success": "#18794f",
    "warn": "#c2234f",
    # voile derrière un panneau, ombre peinte des panneaux
    "backdrop": (24, 18, 40, 92),
    "shadow": (40, 30, 70),
    # pastilles teintées des en-têtes : (fond, trait)
    "f_pink": ("#ffe6ef", "#e0336f"),
    "f_violet": ("#efe8fe", "#6d32e6"),
    "f_neutral": ("#efedf4", "#3c3650"),
}

DARK = {
    "name": "dark",
    "bg": "#141218",
    "panel": "#1d1a24",
    "soft": "#221f2b",
    "soft2": "#2a2734",
    "line": "#2d2937",
    "line2": "#3d3849",
    "hover": "rgba(255, 255, 255, 0.06)",
    "text": "#eeeaf5",
    "text2": "#cdc7da",
    "text_muted": "#a39cb4",
    "text_dim": "#77708a",
    # sur fond sombre, le violet du logo manque de contraste : un violet éclairci
    "accent": "#b48cff",
    "accent2": "#c6a6ff",
    "accent_bg": "#2c2342",
    "accent_line": "#4f3d80",
    "grad_a": "#f03a7e",
    "grad_b": "#6f36e8",
    "grad_a_hover": LOGO_PINK,
    "grad_b_hover": LOGO_VIOLET,
    "progress_a": "#833a60",
    "progress_b": "#4a3386",
    "mkv": "#ff5c95",
    "mp4": "#9a6bff",
    "other": "#5a546b",
    "free": "#2a2734",
    "chart_grid": "rgba(255, 255, 255, 0.07)",
    "zone_alpha": 34,
    "success": "#5fd3a0",
    "warn": "#ff8a9a",
    "backdrop": (6, 4, 12, 150),
    "shadow": (0, 0, 0),
    "f_pink": ("#3a1d2c", "#ff7aa8"),
    "f_violet": ("#2b2147", "#b48cff"),
    "f_neutral": ("#2a2734", "#cdc7da"),
}


def detect_windows_theme() -> str:
    """Return 'light' or 'dark' based on the current Windows apps theme setting."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except OSError:
        return "dark"


def get_palette(name: str) -> dict:
    return LIGHT if name == "light" else DARK


def qcolor(value: str) -> QColor:
    """QColor(str) only understands hex/named colors, not the CSS rgba()/rgb()
    syntax our palettes use for translucency — parse that case manually."""
    if value.startswith("rgba") or value.startswith("rgb"):
        nums = re.findall(r"[\d.]+", value)
        r, g, b = int(float(nums[0])), int(float(nums[1])), int(float(nums[2]))
        a = int(round(float(nums[3]) * 255)) if len(nums) > 3 else 255
        return QColor(r, g, b, a)
    return QColor(value)


def tinted(value: str, alpha: int) -> QColor:
    color = qcolor(value)
    color.setAlpha(alpha)
    return color
