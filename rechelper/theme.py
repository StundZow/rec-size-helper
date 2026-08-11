from __future__ import annotations

import re
import winreg

from PySide6.QtGui import QColor

DARK = {
    "name": "dark",
    "bg_base": "#151024",
    "bg_base2": "#1c1533",
    "blob_colors": ["#7c3aed", "#db2777", "#2563eb", "#0d9488"],
    "blob_alpha": 78,
    "bg": "rgba(0,0,0,0)",
    "card_bg": "rgba(32,26,54,0.38)",
    "card_bg_top": "rgba(52,44,82,0.46)",
    "card_border": "rgba(255,255,255,0.10)",
    "segment_active_bg": "rgba(255,255,255,0.16)",
    "segment_active_text": "#ffffff",
    "chart_grid": "rgba(255,255,255,0.09)",
    "text": "#f4f1fb",
    "text_muted": "#b6adcf",
    "text_dim": "#8d84a6",
    "input_bg": "rgba(255,255,255,0.07)",
    "input_border": "rgba(255,255,255,0.12)",
    "input_border_hover": "rgba(255,255,255,0.25)",
    "groove_bg": "rgba(255,255,255,0.10)",
    "summary_bg": "rgba(219,39,119,0.15)",
    "summary_border": "rgba(236,72,153,0.28)",
    "summary_text": "#ffe2f0",
    "summary_sub": "#e3b8d4",
    "free_segment": "#575070",
    "other_segment": "#a78bfa",
    "storage_track_bg": "rgba(255,255,255,0.08)",
    "storage_gap": "rgba(21,16,36,0.85)",
    "pin_toggle_checked_bg": "rgba(139,92,246,0.25)",
    "pin_toggle_checked_border": "rgba(167,139,250,0.55)",
    "pin_toggle_checked_text": "#e4d9ff",
    "scrollbar_bg": "rgba(255,255,255,0.04)",
    "scrollbar_handle": "rgba(255,255,255,0.16)",
    # modal overlay cards (Settings/Confirm/Pin-edit) need to read as a
    # clearly distinct window over the dimmed+blurred backdrop, so they get
    # a near-solid, deliberately *lighter* fill instead of the translucent
    # glass look regular in-page cards use
    "modal_card_bg": "#3c3260",
}

LIGHT = {
    "name": "light",
    "bg_base": "#f7f3fd",
    "bg_base2": "#edf2fd",
    "blob_colors": ["#a78bfa", "#f472b6", "#60a5fa", "#2dd4bf"],
    "blob_alpha": 105,
    "bg": "rgba(0,0,0,0)",
    "card_bg": "rgba(255,255,255,0.24)",
    "card_bg_top": "rgba(255,255,255,0.34)",
    "card_border": "rgba(255,255,255,0.42)",
    "segment_active_bg": "rgba(255,255,255,0.92)",
    "segment_active_text": "#5b21b6",
    "chart_grid": "rgba(80,60,120,0.10)",
    "text": "#241f38",
    "text_muted": "#665d84",
    "text_dim": "#9d93ba",
    "input_bg": "rgba(255,255,255,0.38)",
    "input_border": "rgba(255,255,255,0.60)",
    "input_border_hover": "rgba(255,255,255,0.90)",
    "groove_bg": "rgba(255,255,255,0.55)",
    "summary_bg": "rgba(249,168,212,0.26)",
    "summary_border": "rgba(244,114,182,0.32)",
    "summary_text": "#7a1e4a",
    "summary_sub": "#a8507e",
    "free_segment": "#c9c2de",
    "other_segment": "#8b5cf6",
    "storage_track_bg": "rgba(255,255,255,0.45)",
    "storage_gap": "rgba(247,243,253,0.85)",
    "pin_toggle_checked_bg": "rgba(139,92,246,0.16)",
    "pin_toggle_checked_border": "rgba(139,92,246,0.45)",
    "pin_toggle_checked_text": "#5b21b6",
    "scrollbar_bg": "rgba(255,255,255,0.2)",
    "scrollbar_handle": "rgba(120,100,160,0.30)",
    "modal_card_bg": "#ffffff",
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
