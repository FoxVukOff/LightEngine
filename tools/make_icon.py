import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QLinearGradient, QPainter, QRadialGradient
from PyQt6.QtWidgets import QApplication

from engine.graphics import Graphics
from engine.mathx import Color, rgb

SIZES = (256, 128, 64, 48, 32, 16)


def draw(size):
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    g = Graphics(p, None)

    bg = QLinearGradient(0, 0, 0, size)
    bg.setColorAt(0.0, QColor(30, 34, 46))
    bg.setColorAt(1.0, QColor(14, 16, 22))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bg))
    p.drawRoundedRect(QRectF(0, 0, size, size), size * 0.22, size * 0.22)

    c = size / 2
    g.glow(c, c * 0.82, size * 0.44, rgb(255, 196, 110, 210), 1.5)
    g.circle(c, c * 0.82, size * 0.15, rgb(255, 244, 214, 255))
    g.circle(c, c * 0.82, size * 0.15, rgb(120, 190, 250, 255), False, size * 0.02)
    g.line(c, c * 0.82 + size * 0.17, c, c * 0.82 + size * 0.36, rgb(120, 200, 245, 255), size * 0.04)
    g.line(c - size * 0.1, c * 0.82 + size * 0.38, c + size * 0.1, c * 0.82 + size * 0.38, rgb(120, 200, 245, 255), size * 0.04)
    p.end()
    return img


def save_ico(pngs):
    # ico с одним png внутри на каждое разрешение
    out = bytearray(struct.pack('<HHH', 0, 1, len(pngs)))
    offset = 6 + 16 * len(pngs)
    for size, data in zip(SIZES, pngs):
        out += struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    for data in pngs:
        out += data
    return bytes(out)


def main():
    app = QApplication.instance() or QApplication([])
    from PyQt6.QtCore import QBuffer, QByteArray
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(here, 'assets')
    os.makedirs(assets, exist_ok=True)

    big = draw(256)
    big.save(os.path.join(assets, 'icon.png'), 'PNG')

    blobs = []
    for s in SIZES:
        store = QByteArray()
        buf = QBuffer(store)
        buf.open(QBuffer.OpenModeFlag.WriteOnly)
        draw(s).save(buf, 'PNG')
        blobs.append(bytes(store))
        buf.close()

    with open(os.path.join(assets, 'icon.ico'), 'wb') as f:
        f.write(save_ico(blobs))
    print('wrote', os.path.join(assets, 'icon.ico'))


if __name__ == '__main__':
    main()
