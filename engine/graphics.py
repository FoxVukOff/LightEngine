from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient

from .mathx import Color

WHITE = Color(1, 1, 1, 1)


def to_qcolor(c, alpha=1.0):
    if c is None:
        return QColor(255, 255, 255, int(alpha * 255))
    if isinstance(c, str):
        q = QColor(c)
        q.setAlphaF(alpha)
        return q
    if isinstance(c, (list, tuple)):
        c = Color(*c)
    if not isinstance(c, Color):
        return QColor(255, 255, 255, int(alpha * 255))
    return QColor.fromRgbF(clamp01(c.r), clamp01(c.g), clamp01(c.b), clamp01(c.a * alpha))


def clamp01(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


class Graphics:
    """сразу-режим рисования, координаты всегда в мире"""

    def __init__(self, painter, res):
        self.p = painter
        self.res = res
        self.font = QFont('Consolas', 11)

    def color(self, c, alpha=1.0):
        return to_qcolor(c, alpha)

    def pen(self, color, width=1.0):
        p = QPen(self.color(color))
        p.setWidthF(max(0.0, float(width)))
        p.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        return p

    def fill(self, brush):
        self.p.setPen(QColor(0, 0, 0, 0))
        self.p.setBrush(QBrush(brush))

    def rect(self, x, y, w, h, color=WHITE, fill=True, width=1.0, ox=0.0, oy=0.0):
        p = self.p
        r = QRectF(x - w * ox, y - h * oy, w, h)
        if fill:
            self.fill(self.color(color))
        else:
            p.setPen(self.pen(color, width))
            p.setBrush(QColor(0, 0, 0, 0))
        p.setBrushOrigin(r.center())
        p.drawRect(r)

    def line(self, x0, y0, x1, y1, color=WHITE, width=1.0):
        p = self.p
        p.setPen(self.pen(color, width))
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))

    def circle(self, x, y, r, color=WHITE, fill=True, width=1.0):
        p = self.p
        rect = QRectF(x - r, y - r, r * 2, r * 2)
        if fill:
            self.fill(self.color(color))
        else:
            p.setPen(self.pen(color, width))
            p.setBrush(QColor(0, 0, 0, 0))
        p.setBrushOrigin(rect.center())
        p.drawEllipse(rect)

    def poly(self, points, color=WHITE, fill=True, width=1.0):
        if len(points) < 2:
            return
        p = self.p
        path = QPainterPath(QPointF(points[0].x, points[0].y))
        for pt in points[1:]:
            path.lineTo(QPointF(pt.x, pt.y))
        path.closeSubpath()
        if fill:
            self.fill(self.color(color))
        else:
            p.setPen(self.pen(color, width))
            p.setBrush(QColor(0, 0, 0, 0))
        p.drawPath(path)

    def text(self, x, y, s, color=WHITE, size=13, align='left', ox=0.0, oy=0.0, font=None):
        p = self.p
        f = QFont(font or self.font)
        f.setPointSizeF(float(size))
        p.setFont(f)
        p.setPen(self.color(color))
        s = str(s)
        w = p.fontMetrics().horizontalAdvance(s)
        p.drawText(QPointF(x - w * ox, y + float(size) * oy), s)

    def sprite(self, name, x, y, w=None, h=None, color=None, angle=0.0, ox=0.5, oy=0.5, alpha=1.0):
        pm = self.res.tinted(name, color) if color is not None else self.res.image(name)
        if pm is None:
            return
        w = float(pm.width()) if w is None else float(w)
        h = float(pm.height()) if h is None else float(h)
        p = self.p
        p.save()
        p.setOpacity(alpha)
        p.translate(x, y)
        if angle:
            p.rotate(angle)
        p.drawPixmap(QRectF(-w * ox, -h * oy, w, h), pm, QRectF(pm.rect()))
        p.restore()

    def gradient_rect(self, x, y, w, h, c0, c1, vertical=True):
        g = QLinearGradient(x, y, x, y + h if vertical else x + w, y)
        g.setColorAt(0.0, self.color(c0))
        g.setColorAt(1.0, self.color(c1))
        p = self.p
        p.setPen(QColor(0, 0, 0, 0))
        p.setBrush(QBrush(g))
        p.setBrushOrigin(QPointF(x + w / 2, y + h / 2))
        p.drawRect(QRectF(x, y, w, h))

    def glow(self, x, y, r, color, power=1.0):
        g = QRadialGradient(QPointF(x, y), max(0.1, r))
        c = color if isinstance(color, Color) else Color(1, 1, 1, 1)
        g.setColorAt(0.0, self.color(c, c.a))
        g.setColorAt(min(0.95, 0.5 * power), self.color(c, c.a * 0.28))
        g.setColorAt(1.0, self.color(c, 0.0))
        p = self.p
        p.save()
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        p.setPen(QColor(0, 0, 0, 0))
        p.setBrush(QBrush(g))
        p.setBrushOrigin(QPointF(x, y))
        p.drawEllipse(QPointF(x, y), r, r)
        p.restore()

    def clip(self, x, y, w, h):
        self.p.save()
        self.p.setClipRect(QRectF(x, y, w, h))

    def restore(self):
        self.p.restore()
