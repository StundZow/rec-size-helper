from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "RecSizeHelper"
PINNED_FILE = CONFIG_DIR / "pinned_folders.json"


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
