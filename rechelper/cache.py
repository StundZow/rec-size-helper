from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "RecSizeHelper" / "cache"


def _cache_path_for_folder(folder: Path) -> Path:
    h = hashlib.sha1(str(folder.resolve()).lower().encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


def load_cache(folder: Path) -> dict:
    path = _cache_path_for_folder(folder)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(folder: Path, cache: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path_for_folder(folder).write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass
