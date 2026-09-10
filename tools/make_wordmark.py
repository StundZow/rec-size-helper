"""Génère `rechelper/assets/wordmark_<theme>.png` : le nom de l'appli rendu en image, en
2x, une par thème.

L'écran de lancement (rechelper/splash.py) ne dessine jamais de texte — sinon il paierait
lui aussi la base de polices Windows (~0,5 s) — donc le nom de l'appli est pré-rendu ici,
une fois, avec la même police que l'interface. À relancer si le nom ou la palette change :

    python tools/make_wordmark.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from rechelper import theme  # noqa: E402

TEXT = "Rec Size Helper"
SCALE = 2
POINT_SIZE = 26  # taille logique ; rendue en 2x pour rester nette sur les écrans HiDPI
PADDING = 6


def render(palette: dict) -> QImage:
    font = QFont("Segoe UI", POINT_SIZE * SCALE)
    font.setWeight(QFont.Weight.Bold)
    metrics = QFontMetricsF(font)
    text_rect = metrics.boundingRect(TEXT)
    width = int(text_rect.width() + 2 * PADDING * SCALE)
    height = int(metrics.height() + 2 * PADDING * SCALE)

    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setFont(font)
    painter.setPen(QColor(palette["text"]))
    painter.drawText(QRectF(0, 0, width, height), Qt.AlignCenter, TEXT)
    painter.end()
    return image


def main():
    QApplication(sys.argv)
    out_dir = ROOT / "rechelper" / "assets"
    for name in ("dark", "light"):
        image = render(theme.get_palette(name))
        path = out_dir / f"wordmark_{name}.png"
        image.save(str(path))
        print(f"{path.name}: {image.width()}x{image.height()}")


if __name__ == "__main__":
    main()
