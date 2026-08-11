from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .cache import load_cache, save_cache
from .models import Recording, VideoFile

MKV_EXT = ".mkv"
MP4_EXT = ".mp4"

_CREATE_NO_WINDOW = 0x08000000


def _find_ffprobe() -> Optional[str]:
    found = shutil.which("ffprobe")
    if found:
        return found
    fallback = Path(r"C:\ffmpeg\bin\ffprobe.exe")
    if fallback.exists():
        return str(fallback)
    return None


FFPROBE = _find_ffprobe()


def get_recording_date(path: Path) -> datetime:
    """Best-effort recording date: embedded creation_time metadata, else file mtime."""
    if FFPROBE:
        try:
            result = subprocess.run(
                [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=_CREATE_NO_WINDOW,
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                tags = data.get("format", {}).get("tags", {}) or {}
                raw = tags.get("creation_time") or tags.get("com.apple.quicktime.creationdate")
                if raw:
                    raw = raw.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(raw)
                    return dt.replace(tzinfo=None)
        except Exception:
            pass
    stat = path.stat()
    return datetime.fromtimestamp(stat.st_mtime)


def _iter_video_paths(folder: Path):
    for dirpath, _dirnames, filenames in os.walk(folder, onerror=lambda e: None):
        for name in filenames:
            ext = Path(name).suffix.lower()
            if ext in (MKV_EXT, MP4_EXT):
                yield Path(dirpath) / name


_SUFFIX_PATTERN = re.compile(
    r"[_\-\s]?(converted|conv|h264|h265|x264|x265|encoded|export|final|reencode|re-encode)$",
    re.IGNORECASE,
)


def _normalize_stem(stem: str) -> str:
    s = stem.strip().lower()
    s = _SUFFIX_PATTERN.sub("", s).strip()
    return s


def pair_recordings(mkv_files: list[VideoFile], mp4_files: list[VideoFile]) -> list[Recording]:
    mkv_by_stem: dict[str, VideoFile] = {}
    for vf in mkv_files:
        mkv_by_stem.setdefault(_normalize_stem(vf.path.stem), vf)

    used_mkv: set[Path] = set()
    used_mp4: set[Path] = set()
    recordings: list[Recording] = []

    # Pass 1: exact (normalized) filename match.
    for mp4 in mp4_files:
        key = _normalize_stem(mp4.path.stem)
        mkv = mkv_by_stem.get(key)
        if mkv and mkv.path not in used_mkv:
            recordings.append(Recording(date=mkv.date, mkv=mkv, mp4=mp4))
            used_mkv.add(mkv.path)
            used_mp4.add(mp4.path)

    # Pass 2: nearest-date match for anything left unpaired (fallback via metadata date).
    remaining_mkv = sorted((f for f in mkv_files if f.path not in used_mkv), key=lambda f: f.date)
    remaining_mp4 = sorted((f for f in mp4_files if f.path not in used_mp4), key=lambda f: f.date)

    MAX_DELTA_HOURS = 6
    matched_mp4_idx: set[int] = set()
    for mkv in remaining_mkv:
        best_idx = None
        best_delta = None
        for idx, mp4 in enumerate(remaining_mp4):
            if idx in matched_mp4_idx:
                continue
            delta = abs((mp4.date - mkv.date).total_seconds()) / 3600
            if delta <= MAX_DELTA_HOURS and (best_delta is None or delta < best_delta):
                best_delta = delta
                best_idx = idx
        if best_idx is not None:
            mp4 = remaining_mp4[best_idx]
            recordings.append(Recording(date=mkv.date, mkv=mkv, mp4=mp4))
            matched_mp4_idx.add(best_idx)
            used_mkv.add(mkv.path)
            used_mp4.add(mp4.path)

    # Pass 3: whatever is left stays solo (no pair found).
    for f in mkv_files:
        if f.path not in used_mkv:
            recordings.append(Recording(date=f.date, mkv=f))
    for f in mp4_files:
        if f.path not in used_mp4:
            recordings.append(Recording(date=f.date, mp4=f))

    recordings.sort(key=lambda r: r.date)
    return recordings


MAX_WORKERS = 8


def scan_folder(
    folder: Path,
    progress: Optional[Callable[[int, int, str], None]] = None,
) -> list[Recording]:
    all_paths = list(_iter_video_paths(folder))
    total = len(all_paths)

    cache = load_cache(folder)
    new_cache: dict[str, dict] = {}
    file_stats: dict[Path, tuple[int, float]] = {}
    dates: dict[Path, datetime] = {}
    to_probe: list[Path] = []

    for p in all_paths:
        try:
            st = p.stat()
        except OSError:
            continue
        file_stats[p] = (st.st_size, st.st_mtime)
        cached = cache.get(str(p))
        if cached and cached.get("size") == st.st_size and cached.get("mtime") == st.st_mtime:
            dates[p] = datetime.fromisoformat(cached["date"])
            new_cache[str(p)] = cached
        else:
            to_probe.append(p)

    done = total - len(to_probe)
    if progress and total:
        progress(done, total, "(depuis le cache)")

    lock = threading.Lock()
    progress_count = done

    def probe_one(p: Path) -> tuple[Path, datetime]:
        return p, get_recording_date(p)

    if to_probe:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(probe_one, p): p for p in to_probe}
            for future in as_completed(futures):
                p, date = future.result()
                dates[p] = date
                size, mtime = file_stats[p]
                new_cache[str(p)] = {"size": size, "mtime": mtime, "date": date.isoformat()}
                if progress:
                    with lock:
                        progress_count += 1
                        progress(progress_count, total, p.name)

    save_cache(folder, new_cache)

    mkv_files: list[VideoFile] = []
    mp4_files: list[VideoFile] = []
    for p, (size, _mtime) in file_stats.items():
        date = dates.get(p)
        if date is None:
            continue
        vf = VideoFile(path=p, size=size, date=date)
        if p.suffix.lower() == MKV_EXT:
            mkv_files.append(vf)
        else:
            mp4_files.append(vf)

    return pair_recordings(mkv_files, mp4_files)
