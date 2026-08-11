from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from .models import Recording
from .theme import DARK

MKV_COLOR = QColor("#ef4444")
MP4_COLOR = QColor("#3b82f6")
ZONE_BOTH = QColor(239, 68, 68, 45)
ZONE_MP4_ONLY = QColor(59, 130, 246, 35)
ZONE_SAFE = QColor(74, 222, 128, 22)
CUTOFF_MKV_LINE = QColor("#ef4444")
CUTOFF_MP4_LINE = QColor("#3b82f6")

MONTHS_FR = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]


def _fmt_gb(num_bytes: float) -> str:
    return f"{num_bytes / (1024 ** 3):.1f} Go".replace(".", ",")


def _fmt_axis_value(value_gb: float) -> str:
    if value_gb >= 1:
        return f"{value_gb:,.0f} Go".replace(",", " ")
    return f"{value_gb * 1024:,.0f} Mo".replace(",", " ")


def _week_start(d: datetime) -> datetime:
    d0 = d.replace(hour=0, minute=0, second=0, microsecond=0)
    return d0 - timedelta(days=d0.weekday())


def _nice_ceil(value: float) -> float:
    if value <= 0:
        return 1.0
    exp = math.floor(math.log10(value))
    frac = value / (10 ** exp)
    if frac <= 1:
        nice = 1
    elif frac <= 2:
        nice = 2
    elif frac <= 5:
        nice = 5
    else:
        nice = 10
    return nice * (10 ** exp)


class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(320)
        self.setMouseTracking(True)
        self.recordings: list[Recording] = []
        self.mp4_cutoff: Optional[datetime] = None
        self.mkv_cutoff: Optional[datetime] = None

        self._buckets: dict[datetime, dict] = {}
        self._weeks: list[datetime] = []
        self._left_date: Optional[datetime] = None
        self._right_date: Optional[datetime] = None
        self._bar_rects: list[tuple[QRectF, datetime, dict]] = []
        self._axis_max_gb = 1.0
        self._palette = DARK

    def set_theme(self, palette: dict):
        self._palette = palette
        self.update()

    def set_recordings(self, recordings: list[Recording]):
        self.recordings = recordings
        self._recompute_buckets()
        self.update()

    def set_cutoffs(self, mp4_cutoff: Optional[datetime], mkv_cutoff: Optional[datetime]):
        self.mp4_cutoff = mp4_cutoff
        self.mkv_cutoff = mkv_cutoff
        self.update()

    def _recompute_buckets(self):
        self._buckets = {}
        self._weeks = []
        if not self.recordings:
            self._left_date = None
            self._right_date = None
            return

        oldest = min(r.date for r in self.recordings)
        now = datetime.now()
        self._left_date = _week_start(oldest)
        self._right_date = now

        weeks = []
        cur = self._left_date
        end = _week_start(now)
        while cur <= end:
            weeks.append(cur)
            cur = cur + timedelta(weeks=1)
        self._weeks = weeks

        buckets = {w: {"mkv": 0, "mp4": 0} for w in weeks}
        for r in self.recordings:
            w = _week_start(r.date)
            if w not in buckets:
                w = weeks[-1] if w > weeks[-1] else weeks[0]
            b = buckets[w]
            if r.mkv:
                b["mkv"] += r.mkv.size
            if r.mp4:
                b["mp4"] += r.mp4.size
        self._buckets = buckets

        max_total_bytes = max((b["mkv"] + b["mp4"] for b in buckets.values()), default=0)
        max_gb = max_total_bytes / (1024 ** 3)
        self._axis_max_gb = _nice_ceil(max_gb) if max_gb > 0 else 1.0

    def _date_to_x(self, date: datetime, left: float, width: float) -> float:
        total = (self._right_date - self._left_date).total_seconds()
        if total <= 0:
            return left
        pos = (date - self._left_date).total_seconds() / total
        pos = max(0.0, min(1.0, pos))
        return left + pos * width

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor(self._palette["chart_bg"]))

        if not self.recordings or self._left_date is None:
            painter.setPen(QColor(self._palette["text_dim"]))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(
                rect, Qt.AlignCenter,
                "Sélectionnez un dossier pour voir la frise de vos enregistrements",
            )
            painter.end()
            return

        margin_left, margin_right = 16, 64
        margin_top, margin_bottom = 16, 56
        chart_rect = QRectF(
            margin_left, margin_top,
            rect.width() - margin_left - margin_right,
            rect.height() - margin_top - margin_bottom,
        )

        # ---- Y axis (right side, in Go) ----
        painter.setPen(QPen(QColor(self._palette["chart_grid"]), 1))
        n_ticks = 4
        for i in range(n_ticks + 1):
            y = chart_rect.bottom() - chart_rect.height() * i / n_ticks
            painter.drawLine(QPointF(chart_rect.left(), y), QPointF(chart_rect.right(), y))

        painter.setPen(QColor(self._palette["text_muted"]))
        painter.setFont(QFont("Segoe UI", 9))
        for i in range(n_ticks + 1):
            y = chart_rect.bottom() - chart_rect.height() * i / n_ticks
            value_gb = self._axis_max_gb * i / n_ticks
            label = _fmt_axis_value(value_gb)
            painter.drawText(QRectF(chart_rect.right() + 6, y - 8, margin_right - 6, 16), Qt.AlignVCenter | Qt.AlignLeft, label)

        # ---- deletion zone shading ----
        if self.mp4_cutoff and self.mkv_cutoff:
            x_mkv = self._date_to_x(self.mkv_cutoff, chart_rect.left(), chart_rect.width())
            x_mp4 = self._date_to_x(self.mp4_cutoff, chart_rect.left(), chart_rect.width())
            x_mkv, x_mp4 = min(x_mkv, x_mp4), max(x_mkv, x_mp4)

            painter.fillRect(QRectF(chart_rect.left(), chart_rect.top(), x_mkv - chart_rect.left(), chart_rect.height()), ZONE_BOTH)
            painter.fillRect(QRectF(x_mkv, chart_rect.top(), x_mp4 - x_mkv, chart_rect.height()), ZONE_MP4_ONLY)
            painter.fillRect(QRectF(x_mp4, chart_rect.top(), chart_rect.right() - x_mp4, chart_rect.height()), ZONE_SAFE)

        # ---- bars (one per ISO week, Monday-based) ----
        self._bar_rects = []
        axis_max_bytes = self._axis_max_gb * (1024 ** 3)
        # Skip every other label once weeks get too numerous to stay readable.
        label_stride = 1 if len(self._weeks) <= 26 else 2 if len(self._weeks) <= 52 else 4
        for idx, w in enumerate(self._weeks):
            b = self._buckets[w]
            bucket_end = w + timedelta(weeks=1)
            x0 = self._date_to_x(w, chart_rect.left(), chart_rect.width())
            x1 = self._date_to_x(bucket_end, chart_rect.left(), chart_rect.width())
            bar_width = max(x1 - x0 - 2, 2)

            total = b["mkv"] + b["mp4"]
            total_h = chart_rect.height() * (total / axis_max_bytes) if axis_max_bytes else 0
            mkv_h = chart_rect.height() * (b["mkv"] / axis_max_bytes) if axis_max_bytes else 0
            mp4_h = total_h - mkv_h
            y_bottom = chart_rect.bottom()

            if b["mkv"] > 0:
                painter.fillRect(QRectF(x0, y_bottom - mkv_h, bar_width, mkv_h), MKV_COLOR)
            if b["mp4"] > 0:
                painter.fillRect(QRectF(x0, y_bottom - mkv_h - mp4_h, bar_width, mp4_h), MP4_COLOR)

            self._bar_rects.append((QRectF(x0, y_bottom - max(total_h, 2), bar_width, max(total_h, 2)), w, b))

            if idx % label_stride != 0:
                continue

            # week tick + label
            painter.setPen(QPen(QColor(self._palette["card_border"]), 1))
            painter.drawLine(QPointF(x0, chart_rect.bottom()), QPointF(x0, chart_rect.bottom() + 5))

            label = f"{w.day} {MONTHS_FR[w.month - 1]}"
            painter.save()
            painter.translate(x0 + bar_width / 2, chart_rect.bottom() + 8)
            painter.rotate(-50)
            painter.setPen(QColor(self._palette["text_muted"]))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(-70, -4, 70, 16), Qt.AlignRight | Qt.AlignVCenter, label)
            painter.restore()

        # ---- cutoff lines ----
        if self.mp4_cutoff and self.mkv_cutoff:
            x_mkv = self._date_to_x(self.mkv_cutoff, chart_rect.left(), chart_rect.width())
            x_mp4 = self._date_to_x(self.mp4_cutoff, chart_rect.left(), chart_rect.width())
            for x, color in ((x_mkv, CUTOFF_MKV_LINE), (x_mp4, CUTOFF_MP4_LINE)):
                pen = QPen(color, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(QPointF(x, chart_rect.top()), QPointF(x, chart_rect.bottom()))

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.position()
        for rect, week_start, b in self._bar_rects:
            wide_rect = QRectF(rect.x(), 0, rect.width(), self.height())
            if wide_rect.contains(pos):
                week_end = week_start + timedelta(days=6)
                label = (
                    f"Semaine du {week_start.day} {MONTHS_FR[week_start.month - 1]} "
                    f"au {week_end.day} {MONTHS_FR[week_end.month - 1]} {week_end.year}"
                )
                text = f"{label}\nMKV : {_fmt_gb(b['mkv'])}\nMP4 : {_fmt_gb(b['mp4'])}\nTotal : {_fmt_gb(b['mkv'] + b['mp4'])}"
                QToolTip.showText(event.globalPosition().toPoint(), text, self)
                return
        QToolTip.hideText()

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)
