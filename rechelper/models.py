from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class VideoFile:
    path: Path
    size: int
    date: datetime


@dataclass
class Recording:
    date: datetime
    mkv: Optional[VideoFile] = None
    mp4: Optional[VideoFile] = None

    @property
    def total_size(self) -> int:
        return (self.mkv.size if self.mkv else 0) + (self.mp4.size if self.mp4 else 0)

    @property
    def age_days(self) -> float:
        return (datetime.now() - self.date).total_seconds() / 86400
