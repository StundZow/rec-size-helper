"""Écran de lancement animé.

Tourne dans un PROCESSUS séparé, pas dans l'appli : le premier rendu de texte d'un
processus Qt sous Windows coûte ~1,5 s (base de polices avec des centaines de familles,
puis la police emoji), et ce coût gèle le thread principal — un verrou du moteur de polices
bloque toute peinture, puis le GIL. Aucune animation ne peut donc tourner *dans* l'appli
pendant qu'elle se charge. Un second processus, lui, n'a rien à attendre.

Pour apparaître tout de suite, cet écran ne dessine que des images et des formes — jamais
de texte, sinon il paierait lui aussi la base de polices. Le nom de l'appli est une image
pré-rendue (`assets/wordmark_*.png`, générée par `tools/make_wordmark.py`).

Protocole avec l'appli, sur l'entrée standard, une ligne par message :
    progress <0-100>    la barre glisse jusqu'à cette valeur
    done                la fenêtre est prête : barre à 100 %, fondu, sortie
Fin de flux sans `done` = l'appli a disparu : on disparaît aussi. Et quoi qu'il arrive, on
ne survit pas plus de SAFETY_TIMEOUT_MS — jamais d'écran de lancement orphelin.
"""

from __future__ import annotations

import math
import os
import sys
import threading
import time

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

from . import settings, theme
from .resources import resource_path

WIDTH, HEIGHT = 420, 290
RADIUS = 24
ICON_SIZE = 96
BAR_WIDTH, BAR_HEIGHT = 250, 6
FRAME_MS = 16
PULSE_PERIOD = 1.8
SHIMMER_PERIOD = 1.4
FADE_MS = 450
SAFETY_TIMEOUT_MS = 20000

# même dégradé que la barre de progression et le bouton de mise à jour de l'appli
_ACCENT_A = QColor("#6366f1")
_ACCENT_B = QColor("#22d3ee")

# mêmes ancrages d'angle que GlassBackground (rel_x, rel_y, rel_radius)
_BLOB_ANCHORS = ((0.03, -0.05, 0.45), (0.97, 0.05, 0.40), (0.90, 1.00, 0.50), (0.06, 0.95, 0.38))


def current_theme_name() -> str:
    return settings.load_settings().get("theme") or theme.detect_windows_theme()


class _StdinReader(QObject):
    """Lit les messages de l'appli dans un thread ; les signaux repassent sur le thread Qt."""

    progress = Signal(int)
    done = Signal()
    closed = Signal()

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            # Dans un exe sans console, sys.stdin peut être None alors que le descripteur 0
            # est bien le tube ouvert par l'appli : on repasse alors par lui directement.
            stream = sys.stdin.buffer if sys.stdin is not None else os.fdopen(0, "rb", buffering=0)
            for raw in iter(stream.readline, b""):
                line = raw.decode("utf-8", "replace").strip()
                if line == "done":
                    self.done.emit()
                    return
                if line.startswith("progress "):
                    try:
                        self.progress.emit(int(line.split()[1]))
                    except (IndexError, ValueError):
                        pass
        except Exception:  # noqa: BLE001 - quoi qu'il arrive, on finit par se fermer
            pass
        self.closed.emit()


class SplashWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WIDTH, HEIGHT)

        name = current_theme_name()
        self._palette = theme.get_palette(name)
        self._icon = QPixmap(resource_path("assets/icon.png")).scaled(
            ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self._wordmark = QPixmap(resource_path(f"assets/wordmark_{name}.png"))

        self._t0 = time.perf_counter()
        self._target = 0.0
        self._shown = 0.0
        self._finishing = False
        self._fade_started: float | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(FRAME_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        screen = QGuiApplication.primaryScreen()
        if screen:
            frame = self.frameGeometry()
            frame.moveCenter(screen.availableGeometry().center())
            self.move(frame.topLeft())

    # ---------------------------------------------------------------- état --
    def set_target(self, percent: int):
        self._target = max(self._target, min(max(percent, 0), 100))

    def finish(self):
        if self._finishing:
            return
        self._finishing = True
        self._target = 100.0

    def on_parent_gone(self):
        if not self._finishing:
            QApplication.instance().quit()

    def _tick(self):
        # La barre glisse vers sa cible au lieu d'y sauter — les cibles, elles, ne
        # bougent que sur de vraies étapes du chargement, jamais sur un minuteur. Une fois
        # l'appli prête, elle finit sa course plus vite, pendant le fondu.
        rate = 0.35 if self._finishing else 0.16
        self._shown += (self._target - self._shown) * rate

        if self._finishing:
            if self._fade_started is None:
                self._fade_started = time.perf_counter()
            progress = (time.perf_counter() - self._fade_started) / (FADE_MS / 1000)
            if progress >= 1.0:
                self._timer.stop()
                QApplication.instance().quit()
                return
            eased = 1 - (1 - progress) ** 3
            self.setWindowOpacity(1.0 - eased)

        self.update()

    # -------------------------------------------------------------- dessin --
    def paintEvent(self, event):
        t = time.perf_counter() - self._t0
        p = self._palette
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        card = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(card, RADIUS, RADIUS)

        base = QLinearGradient(card.topLeft(), card.bottomRight())
        base.setColorAt(0.0, QColor(p["bg_base"]))
        base.setColorAt(1.0, QColor(p["bg_base2"]))
        painter.fillPath(path, base)

        # Taches de couleur dans les angles, comme le fond de l'appli, qui dérivent
        # lentement — restreintes à la carte.
        painter.save()
        painter.setClipPath(path)
        span = max(card.width(), card.height())
        for index, ((ax, ay, ar), color_hex) in enumerate(zip(_BLOB_ANCHORS, p["blob_colors"])):
            phase = index * 2.1
            cx = card.width() * ax + 18 * math.sin(t * 0.55 + phase)
            cy = card.height() * ay + 14 * math.cos(t * 0.45 + phase)
            gradient = QRadialGradient(QPointF(cx, cy), span * ar)
            color = QColor(color_hex)
            color.setAlpha(min(int(p["blob_alpha"] * 1.25), 255))
            edge = QColor(color_hex)
            edge.setAlpha(0)
            gradient.setColorAt(0.0, color)
            gradient.setColorAt(1.0, edge)
            painter.fillRect(card, gradient)
        painter.restore()

        painter.setPen(theme.qcolor(p["card_border"]))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Logo qui respire : opacité et échelle sur un cycle de 1,8 s.
        pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi / PULSE_PERIOD)
        painter.save()
        painter.setOpacity(0.72 + 0.28 * pulse)
        scale = 0.985 + 0.03 * pulse
        icon_center = QPointF(WIDTH / 2, 92)
        painter.translate(icon_center)
        painter.scale(scale, scale)
        painter.translate(-icon_center)
        painter.drawPixmap(
            QPointF(WIDTH / 2 - ICON_SIZE / 2, icon_center.y() - ICON_SIZE / 2), self._icon
        )
        painter.restore()

        # Nom de l'appli : image rendue en 2x, dessinée à sa taille logique.
        if not self._wordmark.isNull():
            logical_w = self._wordmark.width() / 2
            logical_h = self._wordmark.height() / 2
            painter.save()
            painter.setOpacity(0.86 + 0.14 * pulse)
            painter.drawPixmap(
                QRectF(WIDTH / 2 - logical_w / 2, 152, logical_w, logical_h),
                self._wordmark,
                QRectF(self._wordmark.rect()),
            )
            painter.restore()

        # Barre de progression : rainure, remplissage dégradé, reflet qui balaye.
        bar = QRectF(WIDTH / 2 - BAR_WIDTH / 2, 226, BAR_WIDTH, BAR_HEIGHT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(theme.qcolor(p["groove_bg"]))
        painter.drawRoundedRect(bar, BAR_HEIGHT / 2, BAR_HEIGHT / 2)

        fill_w = bar.width() * self._shown / 100
        if fill_w > BAR_HEIGHT:
            fill = QRectF(bar.left(), bar.top(), fill_w, bar.height())
            gradient = QLinearGradient(fill.topLeft(), fill.topRight())
            gradient.setColorAt(0.0, _ACCENT_A)
            gradient.setColorAt(1.0, _ACCENT_B)
            painter.setBrush(gradient)
            painter.drawRoundedRect(fill, BAR_HEIGHT / 2, BAR_HEIGHT / 2)

            shimmer_path = QPainterPath()
            shimmer_path.addRoundedRect(fill, BAR_HEIGHT / 2, BAR_HEIGHT / 2)
            painter.save()
            painter.setClipPath(shimmer_path)
            band_w = bar.width() * 0.35
            sweep = (t % SHIMMER_PERIOD) / SHIMMER_PERIOD
            band_x = bar.left() - band_w + (bar.width() + 2 * band_w) * sweep
            band = QLinearGradient(QPointF(band_x, 0), QPointF(band_x + band_w, 0))
            band.setColorAt(0.0, QColor(255, 255, 255, 0))
            band.setColorAt(0.5, QColor(255, 255, 255, 90))
            band.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillRect(fill, band)
            painter.restore()

        painter.end()


def run_splash() -> int:
    app = QApplication(sys.argv)
    window = SplashWindow()
    window.show()

    reader = _StdinReader()
    reader.progress.connect(window.set_target)
    reader.done.connect(window.finish)
    reader.closed.connect(window.on_parent_gone)
    reader.start()

    QTimer.singleShot(SAFETY_TIMEOUT_MS, window.finish)
    return app.exec()
