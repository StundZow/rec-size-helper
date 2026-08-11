from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from . import update_config
from .__version__ import VERSION

_CREATE_NO_WINDOW = 0x08000000
_CREATE_NEW_PROCESS_GROUP = 0x00000200


def parse_version(v: str) -> tuple[int, ...]:
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def is_newer(remote: str, local: str = VERSION) -> bool:
    return parse_version(remote) > parse_version(local)


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


class UpdateInfo:
    def __init__(self, tag: str, notes: str, download_url: str, size: int):
        self.tag = tag
        self.version = tag.lstrip("vV")
        self.notes = notes
        self.download_url = download_url
        self.size = size


class UpdateCheckWorker(QThread):
    found = Signal(object)   # UpdateInfo
    not_found = Signal()
    error = Signal(str)

    def run(self):
        if not update_config.is_configured():
            self.error.emit("Dépôt GitHub non configuré.")
            return
        url = (
            f"https://api.github.com/repos/{update_config.GITHUB_OWNER}"
            f"/{update_config.GITHUB_REPO}/releases/latest"
        )
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            self.error.emit(str(e))
            return

        tag = data.get("tag_name", "")
        if not tag or not is_newer(tag):
            self.not_found.emit()
            return

        asset = next(
            (a for a in data.get("assets", []) if a.get("name") == update_config.ASSET_NAME),
            None,
        )
        if not asset:
            self.error.emit("Aucun exécutable trouvé dans la dernière release.")
            return

        info = UpdateInfo(
            tag=tag,
            notes=data.get("body", "") or "",
            download_url=asset["browser_download_url"],
            size=asset.get("size", 0),
        )
        self.found.emit(info)


class DownloadWorker(QThread):
    progress = Signal(int, int)   # bytes_done, bytes_total
    finished_download = Signal(str)  # path to downloaded file
    error = Signal(str)

    def __init__(self, url: str, dest_path: Path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={"User-Agent": "RecSizeHelper-Updater"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                done = 0
                with open(self.dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        self.progress.emit(done, total)
            self.finished_download.emit(str(self.dest_path))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            self.error.emit(str(e))


def launch_self_update(new_exe_path: Path) -> None:
    """Swaps the running exe for the freshly downloaded one, then relaunches it.

    Only meaningful for a frozen (PyInstaller) build — the running exe can't
    overwrite itself while it's still open, so a tiny detached batch script
    waits for this process to fully exit, then moves the new file into place.
    """
    current_exe = Path(sys.executable)
    bat_path = Path(tempfile.gettempdir()) / "rec_size_helper_update.bat"
    bat_content = f"""@echo off
:waitproc
tasklist /FI "IMAGENAME eq {current_exe.name}" 2>NUL | find /I "{current_exe.name}" >NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto waitproc
)

set RETRY=0
:trymove
move /Y "{new_exe_path}" "{current_exe}" > nul 2>&1
if exist "{new_exe_path}" (
    set /a RETRY+=1
    if %RETRY% LSS 20 (
        timeout /t 1 /nobreak > nul
        goto trymove
    )
)

start "" "{current_exe}"
del "%~f0"
"""
    bat_path.write_text(bat_content, encoding="utf-8")
    # CREATE_NO_WINDOW still allocates a (hidden) console, which the batch
    # file's tasklist/find/timeout commands need to function — a fully
    # DETACHED_PROCESS has no console at all and makes them fail silently.
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=_CREATE_NEW_PROCESS_GROUP | _CREATE_NO_WINDOW,
        close_fds=True,
    )
