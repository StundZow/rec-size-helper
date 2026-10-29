"""Génère l'icône de l'appli à partir de son dessin vectoriel (le SVG ci-dessous) :
`rechelper/assets/icon.ico` (toutes les tailles qu'utilise Windows), `rechelper/assets/icon.png`
(écran de lancement, installateur) et `icon.png` à la racine (README).

Le dessin : une tuile pleine en dégradé rose → violet (la palette de l'appli) et un glyphe
blanc, un point REC entouré d'une jauge de stockage en deux tons (MKV puis MP4). Jusqu'à
24 px, une variante simplifiée (jauge d'un seul tenant, traits plus épais, tuile bord à bord)
reste nette. À relancer après toute retouche du dessin :

    python tools/make_icon.py
"""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "rechelper" / "assets"

TOP_LEFT, BOTTOM_RIGHT = "#FF4F8B", "#7B3FF2"
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
SMALL_MAX = 24
PNG_SIZE = 512

# Les parties estompées sont peintes avec le dégradé de la tuile éclairci (url(#w26) : mêlé
# à 26 % de blanc) plutôt qu'en blanc translucide, pour que leurs chevauchements ne se voient pas.
ICON = """
<circle cx="512" cy="512" r="262" fill="none" stroke="url(#w26)" stroke-width="96"/>
<path d="M512 250 A262 262 0 0 1 643 738.9" fill="none" stroke="#fff" stroke-width="96" stroke-linecap="round"/>
<path d="M502.9 773.8 A262 262 0 0 1 285.1 643" fill="none" stroke="url(#w62)" stroke-width="96" stroke-linecap="round"/>
<circle cx="512" cy="512" r="124" fill="#fff"/>
"""

SMALL = """
<circle cx="512" cy="512" r="250" fill="none" stroke="url(#w32)" stroke-width="128"/>
<path d="M512 262 A250 250 0 1 1 307.2 655.4" fill="none" stroke="#fff" stroke-width="128" stroke-linecap="round"/>
<circle cx="512" cy="512" r="132" fill="#fff"/>
"""


def lighten(color: str, amount: float) -> str:
    rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(c + (255 - c) * amount):02x}" for c in rgb)


def gradient(gid: str, start: str, end: str, inset: int) -> str:
    far = 1024 - inset
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{inset}" y1="{inset}" x2="{far}" y2="{far}">'
        f'<stop offset="0" stop-color="{start}"/><stop offset="1" stop-color="{end}"/></linearGradient>'
    )


def svg(glyph: str, inset: int = 32) -> str:
    """La tuile (carré arrondi, dégradé en diagonale), le glyphe, puis un halo discret en
    haut à gauche posé par-dessus le tout."""
    tints = "".join(
        gradient(f"w{p}", lighten(TOP_LEFT, int(p) / 100), lighten(BOTTOM_RIGHT, int(p) / 100), inset)
        for p in sorted(set(re.findall(r"url\(#w(\d+)\)", glyph)))
    )
    side = 1024 - 2 * inset
    radius = round(side * 0.233)
    tile = f'<rect x="{inset}" y="{inset}" width="{side}" height="{side}" rx="{radius}"'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><defs>
{gradient("bg", TOP_LEFT, BOTTOM_RIGHT, inset)}{tints}
<radialGradient id="sheen" gradientUnits="userSpaceOnUse" cx="260" cy="120" r="900">
<stop offset="0" stop-color="#fff" stop-opacity="0.16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</radialGradient></defs>
{tile} fill="url(#bg)"/>{glyph}{tile} fill="url(#sheen)"/></svg>"""


def render(svg_text: str, size: int) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(svg_text.encode())).render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image.convertToFormat(QImage.Format_ARGB32)


def png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def dib_bytes(image: QImage) -> bytes:
    """Bitmap 32 bits BGRA (lignes de bas en haut) suivi du masque AND : le format historique
    des .ico, lu par tout ce qui sait lire une icône."""
    size = image.width()
    stride = size * 4
    pixels = bytes(image.constBits())[: stride * size]
    rows = [pixels[y * stride:(y + 1) * stride] for y in reversed(range(size))]
    mask_stride = (size + 31) // 32 * 4
    mask = bytearray()
    for row in rows:
        bits = bytearray(mask_stride)
        for x in range(size):
            if row[x * 4 + 3] == 0:
                bits[x // 8] |= 0x80 >> (x % 8)
        mask += bits
    header = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, stride * size + len(mask), 0, 0, 0, 0)
    return header + b"".join(rows) + bytes(mask)


def write_ico(path: Path, frames: list[QImage]) -> None:
    # 256 px en PNG (seul format que Windows attend à cette taille), le reste en bitmap
    blobs = [png_bytes(f) if f.width() >= 256 else dib_bytes(f) for f in frames]
    offset = 6 + 16 * len(frames)
    entries = b""
    for frame, blob in zip(frames, blobs):
        side = frame.width() % 256  # 256 s'écrit 0
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    path.write_bytes(struct.pack("<HHH", 0, 1, len(frames)) + entries + b"".join(blobs))


def main():
    QGuiApplication(sys.argv)
    icon, small = svg(ICON), svg(SMALL, inset=0)
    frames = [render(small if size <= SMALL_MAX else icon, size) for size in ICO_SIZES]
    write_ico(ASSETS / "icon.ico", frames)
    print(f"icon.ico: {', '.join(map(str, ICO_SIZES))} px")
    image = render(icon, PNG_SIZE)
    for path in (ASSETS / "icon.png", ROOT / "icon.png"):
        image.save(str(path))
        print(f"{path.relative_to(ROOT)}: {PNG_SIZE}x{PNG_SIZE}")


if __name__ == "__main__":
    main()
