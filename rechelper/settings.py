from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "RecSizeHelper"
PINNED_FILE = CONFIG_DIR / "pinned_folders.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# theme: None means "follow Windows", otherwise "dark"/"light" (last explicit choice)
DEFAULT_SETTINGS = {"theme": None, "auto_lock_mkv": True}
DEFAULT_PIN_ICON = "📁"


def load_pinned_folders() -> list[dict]:
    if not PINNED_FILE.exists():
        return []
    try:
        data = json.loads(PINNED_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        result = []
        for item in data:
            # older versions stored plain path strings — migrate on read
            if isinstance(item, str):
                result.append({"path": item, "name": Path(item).name or item, "icon": DEFAULT_PIN_ICON})
            elif isinstance(item, dict) and item.get("path"):
                path = str(item["path"])
                result.append({
                    "path": path,
                    "name": str(item.get("name") or Path(path).name or path),
                    "icon": str(item.get("icon") or DEFAULT_PIN_ICON),
                })
        return result
    except Exception:
        pass
    return []


def save_pinned_folders(folders: list[dict]) -> None:
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
