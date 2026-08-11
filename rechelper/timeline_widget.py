from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from .models import Recording
from .theme import DARK, qcolor

MKV_STROKE = QColor("#ef4444")
MP4_STROKE = QColor("#3b82f6")
MKV_FILL_TOP = QColor(239, 68, 68, 72)
MP4_FILL_TOP = QColor(59, 130, 246, 72)

MONTHS_FR = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]


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


def _smooth_path(points: list[QPointF], baseline_y: float) -> QPainterPath:
    """Catmull-Rom spline through the points, converted to cubic Beziers.

    Control points are clamped to the baseline so the curve can never
    undershoot below zero — empty weeks hug the axis instead of dipping
    under the month labels.
    """
    path = QPainterPath()
    if not points:
        return path
    path.moveTo(points[0])
    if len(points) == 1:
        return path
    n = len(points)
    for i in range(n - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[i + 2] if i + 2 < n else points[i + 1]
        c1 = QPointF(p1.x() + (p2.x() - p0.x()) / 6.0,
                     min(p1.y() + (p2.y() - p0.y()) / 6.0, baseline_y))
        c2 = QPointF(p2.x() - (p3.x() - p1.x()) / 6.0,
                     min(p2.y() - (p3.y() - p1.y()) / 6.0, baseline_y))
        path.cubicTo(c1, c2, p2)
    return path


class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.recordings: list[Recording] = []
        self.mp4_cutoff: Optional[datetime] = None
        self.mkv_cutoff: Optional[datetime] = None

        self._weeks: list[datetime] = []
        self._mkv_vals: list[float] = []
        self._mp4_vals: list[float] = []
        self._left_date: Optional[datetime] = None
        self._right_date: Optional[datetime] = None
        self._axis_max_gb = 1.0
        self._palette = DARK

        # entrance animation: curves rise from the baseline
        self._reveal = 1.0
        self._reveal_anim = QVariantAnimation(self)
        self._reveal_anim.setDuration(700)
        self._reveal_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._reveal_anim.setStartValue(0.0)
        self._reveal_anim.setEndValue(1.0)
        self._reveal_anim.valueChanged.connect(self._on_reveal_tick)

        # cutoff highlights glide smoothly instead of jumping with the slider
        self._mp4_x_ts: Optional[float] = None
        self._mkv_x_ts: Optional[float] = None
        self._mp4_anim = self._make_cutoff_anim("_mp4_x_ts")
        self._mkv_anim = self._make_cutoff_anim("_mkv_x_ts")

    def _make_cutoff_anim(self, attr: str) -> QVariantAnimation:
        anim = QVariantAnimation(self)
        anim.setDuration(170)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(lambda v, a=attr: (setattr(self, a, float(v)), self.update()))
        return anim

    def _on_reveal_tick(self, value):
        self._reveal = float(value)
        self.update()

    def set_theme(self, palette: dict):
        self._palette = palette
        self.update()

    def set_recordings(self, recordings: list[Recording]):
        self.recordings = recordings
        self._recompute_buckets()
        self._reveal_anim.stop()
        self._reveal = 0.0
        self._reveal_anim.start()

    def set_cutoffs(self, mp4_cutoff: Optional[datetime], mkv_cutoff: Optional[datetime]):
        self.mp4_cutoff = mp4_cutoff
        self.mkv_cutoff = mkv_cutoff
        if mp4_cutoff is None or mkv_cutoff is None or not self._weeks:
            self._mp4_x_ts = None
            self._mkv_x_ts = None
            self.update()
            return

        mp4_ts = mp4_cutoff.timestamp()
        mkv_ts = mkv_cutoff.timestamp()
        if self._mp4_x_ts is None:
            self._mp4_x_ts = mp4_ts
            self._mkv_x_ts = mkv_ts
            self.update()
            return

        for anim, current, target in (
            (self._mp4_anim, self._mp4_x_ts, mp4_ts),
            (self._mkv_anim, self._mkv_x_ts, mkv_ts),
        ):
            anim.stop()
            anim.setStartValue(float(current))
            anim.setEndValue(float(target))
            anim.start()

    def _recompute_buckets(self):
        self._weeks = []
        self._mkv_vals = []
        self._mp4_vals = []
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

        buckets = {w: [0.0, 0.0] for w in weeks}
        for r in self.recordings:
            w = _week_start(r.date)
            if w not in buckets:
                w = weeks[-1] if w > weeks[-1] else weeks[0]
            if r.mkv:
                buckets[w][0] += r.mkv.size
            if r.mp4:
                buckets[w][1] += r.mp4.size
        self._mkv_vals = [buckets[w][0] for w in weeks]
        self._mp4_vals = [buckets[w][1] for w in weeks]

        max_bytes = max([*self._mkv_vals, *self._mp4_vals], default=0)
        max_gb = max_bytes / (1024 ** 3)
        self._axis_max_gb = _nice_ceil(max_gb) if max_gb > 0 else 1.0

    def _ts_to_x(self, ts: float, left: float, width: float) -> float:
        t0 = self._left_date.timestamp()
        t1 = self._right_date.timestamp()
        if t1 <= t0:
            return left
        pos = (ts - t0) / (t1 - t0)
        return left + max(0.0, min(1.0, pos)) * width

    def _curve_y_at(self, xs: list[float], vals: list[float], x: float,
                    bottom: float, height: float, axis_max: float) -> float:
        """Linear interpolation of a series' y position at an arbitrary x."""
        if not xs:
            return bottom
        if x <= xs[0]:
            v = vals[0]
        elif x >= xs[-1]:
            v = vals[-1]
        else:
            v = vals[-1]
            for i in range(len(xs) - 1):
                if xs[i] <= x <= xs[i + 1]:
                    span = xs[i + 1] - xs[i]
                    f = (x - xs[i]) / span if span else 0.0
                    v = vals[i] + (vals[i + 1] - vals[i]) * f
                    break
        return bottom - height * (v / axis_max) * self._reveal

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        if not self.recordings or self._left_date is None:
            painter.setPen(qcolor(self._palette["text_dim"]))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(
                rect, Qt.AlignCenter,
                "Sélectionnez un dossier pour voir la courbe de vos enregistrements",
            )
            painter.end()
            return

        margin_left, margin_right = 16, 64
        margin_top, margin_bottom = 20, 56
        chart_rect = QRectF(
            margin_left, margin_top,
            rect.width() - margin_left - margin_right,
            rect.height() - margin_top - margin_bottom,
        )
        axis_max_bytes = self._axis_max_gb * (1024 ** 3)

        # ---- horizontal grid + right-side axis labels ----
        painter.setPen(QPen(qcolor(self._palette["chart_grid"]), 1))
        n_ticks = 4
        for i in range(n_ticks + 1):
            y = chart_rect.bottom() - chart_rect.height() * i / n_ticks
            painter.drawLine(QPointF(chart_rect.left(), y), QPointF(chart_rect.right(), y))

        painter.setPen(qcolor(self._palette["text_muted"]))
        painter.setFont(QFont("Segoe UI", 9))
        for i in range(n_ticks + 1):
            y = chart_rect.bottom() - chart_rect.height() * i / n_ticks
            label = _fmt_axis_value(self._axis_max_gb * i / n_ticks)
            painter.drawText(QRectF(chart_rect.right() + 6, y - 8, margin_right - 6, 16),
                             Qt.AlignVCenter | Qt.AlignLeft, label)

        # ---- week columns: dashed vertical gridlines + bottom labels ----
        n_weeks = len(self._weeks)
        label_stride = 1 if n_weeks <= 26 else 2 if n_weeks <= 52 else 4
        week_span = timedelta(weeks=1).total_seconds()
        xs: list[float] = []
        for idx, w in enumerate(self._weeks):
            x_center = self._ts_to_x(w.timestamp() + week_span / 2, chart_rect.left(), chart_rect.width())
            xs.append(x_center)

            if idx % label_stride != 0:
                continue

            dash_pen = QPen(qcolor(self._palette["chart_grid"]), 1, Qt.DashLine)
            painter.setPen(dash_pen)
            painter.drawLine(QPointF(x_center, chart_rect.top()), QPointF(x_center, chart_rect.bottom()))

            label = f"{w.day} {MONTHS_FR[w.month - 1]}"
            painter.save()
            painter.translate(x_center, chart_rect.bottom() + 10)
            painter.rotate(-50)
            painter.setPen(qcolor(self._palette["text_muted"]))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(-70, -4, 70, 16), Qt.AlignRight | Qt.AlignVCenter, label)
            painter.restore()

        # ---- deletion zones: soft colour glow showing what's selected ----
        # left of the red line = MKV + MP4 deleted (red glow); between red and
        # blue = MP4 only (blue glow); right of blue = kept (no glow).
        if self._mkv_x_ts is not None and self._mp4_x_ts is not None:
            x_mkv = self._ts_to_x(self._mkv_x_ts, chart_rect.left(), chart_rect.width())
            x_mp4 = self._ts_to_x(self._mp4_x_ts, chart_rect.left(), chart_rect.width())
            x_red = min(x_mkv, x_mp4)
            x_blue = max(x_mkv, x_mp4)
            painter.save()
            painter.setClipRect(chart_rect)

            def glow_zone(x_start: float, x_end: float, color: QColor):
                if x_end <= x_start:
                    return
                base = QColor(color)
                base.setAlpha(16)
                painter.fillRect(QRectF(x_start, chart_rect.top(), x_end - x_start, chart_rect.height()), base)
                band_w = min(80.0, x_end - x_start)
                grad = QLinearGradient(x_end - band_w, 0, x_end, 0)
                g0 = QColor(color)
                g0.setAlpha(0)
                g1 = QColor(color)
                g1.setAlpha(46)
                grad.setColorAt(0.0, g0)
                grad.setColorAt(1.0, g1)
                painter.fillRect(QRectF(x_end - band_w, chart_rect.top(), band_w, chart_rect.height()), grad)

            glow_zone(chart_rect.left(), x_red, MKV_STROKE)
            glow_zone(x_red, x_blue, MP4_STROKE)
            painter.restore()

        # ---- the two smooth area curves ----
        def draw_series(vals: list[float], stroke: QColor, fill_top: QColor):
            pts = [
                QPointF(x, chart_rect.bottom() - chart_rect.height() * (v / axis_max_bytes) * self._reveal)
                for x, v in zip(xs, vals)
            ]
            if len(pts) == 1:
                pts = [QPointF(chart_rect.left(), pts[0].y()), QPointF(chart_rect.right(), pts[0].y())]
            else:
                # points sit at each week's *center*, which leaves a gap
                # between the chart edge and the first/last week — extend
                # flat to both edges so the curve fills the whole axis.
                if pts[0].x() > chart_rect.left():
                    pts = [QPointF(chart_rect.left(), pts[0].y())] + pts
                if pts[-1].x() < chart_rect.right():
                    pts = pts + [QPointF(chart_rect.right(), pts[-1].y())]
            curve = _smooth_path(pts, chart_rect.bottom())

            fill = QPainterPath(curve)
            fill.lineTo(pts[-1].x(), chart_rect.bottom())
            fill.lineTo(pts[0].x(), chart_rect.bottom())
            fill.closeSubpath()
            # anchor the fade to the curve's own peak, not the chart top —
            # otherwise dips carry a grey wash that reads as a rendering bug
            peak_y = min(p.y() for p in pts)
            grad = QLinearGradient(0, peak_y, 0, chart_rect.bottom())
            grad.setColorAt(0.0, fill_top)
            end = QColor(fill_top)
            end.setAlpha(0)
            grad.setColorAt(1.0, end)
            painter.fillPath(fill, grad)

            pen = QPen(stroke, 2.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(curve)

        painter.save()
        painter.setClipRect(chart_rect)
        draw_series(self._mkv_vals, MKV_STROKE, MKV_FILL_TOP)
        draw_series(self._mp4_vals, MP4_STROKE, MP4_FILL_TOP)
        painter.restore()

        # ---- cutoff highlights: soft glow band + core line + dot on curve ----
        def draw_highlight(ts: Optional[float], color: QColor, vals: list[float]):
            if ts is None:
                return
            x = self._ts_to_x(ts, chart_rect.left(), chart_rect.width())
            band_w = 30.0
            band = QLinearGradient(x - band_w / 2, 0, x + band_w / 2, 0)
            edge = QColor(color)
            edge.setAlpha(0)
            mid = QColor(color)
            mid.setAlpha(46)
            band.setColorAt(0.0, edge)
            band.setColorAt(0.5, mid)
            band.setColorAt(1.0, edge)
            painter.fillRect(QRectF(x - band_w / 2, chart_rect.top(), band_w, chart_rect.height()), band)

            core = QColor(color)
            core.setAlpha(215)
            painter.setPen(QPen(core, 2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(x, chart_rect.top()), QPointF(x, chart_rect.bottom()))

            y = self._curve_y_at(xs, vals, x, chart_rect.bottom(), chart_rect.height(), axis_max_bytes)
            painter.setPen(QPen(QColor(255, 255, 255, 235), 2))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), 5, 5)

        draw_highlight(self._mkv_x_ts, MKV_STROKE, self._mkv_vals)
        draw_highlight(self._mp4_x_ts, MP4_STROKE, self._mp4_vals)

        painter.end()
