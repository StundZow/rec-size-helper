from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "RecSizeHelper"
PINNED_FILE = CONFIG_DIR / "pinned_folders.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# theme: None means "follow Windows", otherwise "dark"/"light" (last explicit choice)
DEFAULT_SETTINGS = {"theme": None, "auto_lock_mkv": True}


def load_pinned_folders() -> list[str]:
    if not PINNED_FILE.exists():
        return []
    try:
        data = json.loads(PINNED_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(p) for p in data]
    except Exception:
        pass
    return []


def save_pinned_folders(folders: list[str]) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        PINNED_FILE.write_text(json.dumps(folders), encoding="utf-8")
    except OSError:
        pass


def load_settings() -> dict:
    merged = dict(DEFAULT_SETTINGS)
    if not SETTINGS_FILE.exists():
        return merged
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            merged.update(data)
    except Exception:
        pass
    return merged


def save_settings(data: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass
