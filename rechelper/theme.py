from __future__ import annotations

import winreg

DARK = {
    "name": "dark",
    "bg": "#0b0d12",
    "card_bg": "#161923",
    "card_border": "#232838",
    "chart_bg": "#12141c",
    "chart_grid": "#232838",
    "text": "#e6e9f0",
    "text_muted": "#8b93a7",
    "text_dim": "#565b6c",
    "input_bg": "#1c2030",
    "input_border": "#2c3247",
    "input_border_hover": "#3a4162",
    "groove_bg": "#1c2030",
    "summary_bg": "#1f1720",
    "summary_border": "#4a3040",
    "summary_text": "#ffe8ee",
    "summary_sub": "#d9b8c6",
    "free_segment": "#454b61",
    "other_segment": "#8b5cf6",
    "storage_track_bg": "#20242f",
    "storage_gap": "#12141c",
    "pin_toggle_checked_bg": "#2a1f3d",
    "pin_toggle_checked_border": "#8b5cf6",
    "pin_toggle_checked_text": "#d6c8ff",
    "scrollbar_bg": "#12141c",
    "scrollbar_handle": "#2c3247",
}

LIGHT = {
    "name": "light",
    "bg": "#eef0f5",
    "card_bg": "#ffffff",
    "card_border": "#dde1ea",
    "chart_bg": "#ffffff",
    "chart_grid": "#e5e8f0",
    "text": "#191b22",
    "text_muted": "#5b6172",
    "text_dim": "#9aa0b1",
    "input_bg": "#eef0f6",
    "input_border": "#d7dbe6",
    "input_border_hover": "#c0c6d6",
    "groove_bg": "#e2e5ee",
    "summary_bg": "#fff0f5",
    "summary_border": "#f3c4d6",
    "summary_text": "#7a1e3a",
    "summary_sub": "#a8506e",
    "free_segment": "#c7cbd8",
    "other_segment": "#8b5cf6",
    "storage_track_bg": "#eef0f6",
    "storage_gap": "#ffffff",
    "pin_toggle_checked_bg": "#ece5ff",
    "pin_toggle_checked_border": "#8b5cf6",
    "pin_toggle_checked_text": "#5b21b6",
    "scrollbar_bg": "#eef0f5",
    "scrollbar_handle": "#c7cbd8",
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
