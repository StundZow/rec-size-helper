from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative: str) -> str:
    """Resolve a bundled resource path, both when run from source and from a
    PyInstaller --onefile build (where assets are unpacked into sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return str(Path(base) / "rechelper" / relative)
    return str(Path(__file__).parent / relative)


ICON_PATH = resource_path("assets/icon.ico")
