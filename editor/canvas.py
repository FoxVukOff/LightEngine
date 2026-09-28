from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QMenu, QWidget

from engine.graphics import to_qcolor
from engine.input import key_name
from engine.mathx import Color, Vec, clamp

SEL = Color(0.32, 0.78, 1.0, 1.0)
GRID = Color(1, 1, 1, 0.045)
GRID_BIG = Color(1, 1, 1, 0.1)
AXIS = Color(1, 0.45, 0.45, 0.35)
AXIS2 = Color(0.45, 0.85, 0.55, 0.35)


class Canvas(QWidget):
    selected = pyqtSignal(object)
    moved = pyqtSignal(object)
    edited = pyqtSignal()
    request = pyqtSignal(str)

    def __init__(self, win):
        QWidget.__init__(self)
        self.win = win
        self.pan = Vec(0, 0)
        self.zoom = 1.0
        self.snap = True
        self.show_grid = True
        self.sel = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 200)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._mode = None
        self._off = Vec(0, 0)
        self._press = Vec(0, 0)
        self._box = None
        self._space = False

    def scene(self):
        return self.win.scene

    def game(self):
        return self.win.game

    def view_tuple(self):
        return (self.pan.x, self.pan.y, self.zoom)

    # --- преобразования ---

    def to_world(self, sx, sy):
        return Vec((sx - self.width() / 2) / self.zoom + self.pan.x,
                   (sy - self.height() / 2) / self.zoom + self.pan.y)

    def to_screen(self, wx, wy):
        return Vec((wx - self.pan.x) * self.zoom + self.width() / 2,
                   (wy - self.pan.y) * self.zoom + self.height() / 2)

    def frame_all(self):
        nodes = [n for n in self.scene().walk() if n.bounds() is not None]
        if not nodes:
            self.pan = Vec(0, 0)
            self.zoom = 1.0
            return
        xs, ys, xe, ye = [], [], [], []
        for n in nodes:
            x, y, w, h = n.bounds()
            xs.append(x)
            ys.append(y)
            xe.append(x + w)
            ye.append(y + h)
        self.pan = Vec((min(xs) + max(xe)) / 2, (min(ys) + max(ye)) / 2)
        w = max(1.0, max(xe) - min(xs))
        h = max(1.0, max(ye) - min(ys))
        self.zoom = clamp(min(self.width() / (w * 1.25), self.height() / (h * 1.25)), 0.05, 8.0)
        self.update()

    def frame_node(self, n):
        if n is None or n.bounds() is None:
            return
        x, y, w, h = n.bounds()
        self.pan = Vec(x + w / 2, y + h / 2)
        self.update()

    def zoom_by(self, f, sx=None, sy=None):
        sx = self.width() / 2 if sx is None else sx
        sy = self.height() / 2 if sy is None else sy
        before = self.to_world(sx, sy)
        self.zoom = clamp(self.zoom * f, 0.05, 16.0)
        after = self.to_world(sx, sy)
        self.pan = self.pan + (before - after)
        self.update()

    # --- отрисовка ---

    def paintEvent(self, ev):
        try:
            self.paint()
        except Exception as err:
            self.win.log('draw error: %s' % err)
            p = QPainter(self)
            p.setPen(QColor(255, 120, 120))
            p.drawText(QPointF(10, 20), 'draw error: %s' % err)
            p.end()

    def paint(self):
        p = QPainter(self)
        size = Vec(self.width(), self.height())
        g = self.game()
        playing = self.win.playing
        p.fillRect(0, 0, self.width(), self.height(), to_qcolor(self.scene().bg))
        p.save()
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(self.zoom, self.zoom)
        p.translate(-self.pan.x, -self.pan.y)
        if self.show_grid and not playing:
            self.draw_grid(p, size)
        g.render(p, size, scripts=playing, view=self.view_tuple(), use_camera=playing)
        if not playing:
            self.draw_overlay(p)
        p.restore()
        if playing:
            self.draw_hud(p)
        self.draw_frame(p)
        if self.win.project is None:
            self.draw_noproject(p)
        p.end()

    def draw_noproject(self, p):
        p.setPen(QPen(to_qcolor(Color(1, 1, 1, 0.35))))
        f = p.font()
        f.setPointSizeF(15.0)
        p.setFont(f)
        p.drawText(QPointF(self.width() / 2, self.height() / 2 - 10),
                   'проект не выбран')
        p.setFont(self.font())
        p.setPen(QPen(to_qcolor(Color(1, 1, 1, 0.25))))
        p.drawText(QPointF(self.width() / 2, self.height() / 2 + 14),
                   'file -> new project... или ctrl+shift+n')

    def draw_grid(self, p, size):
        step = self.scene().grid or 32
        if step * self.zoom < 6:
            step *= 4
        x0 = int((self.pan.x - size.x / 2 / self.zoom) // step) * step
        x1 = self.pan.x + size.x / 2 / self.zoom
        y0 = int((self.pan.y - size.y / 2 / self.zoom) // step) * step
        y1 = self.pan.y + size.y / 2 / self.zoom
        big = max(1, int(8 * 32 / step))
        x = x0
        while x <= x1:
            pen = QPen(to_qcolor(GRID_BIG if (int(round(x / step)) % big) == 0 else GRID))
            pen.setWidthF(1.0 / self.zoom)
            p.setPen(pen)
            p.drawLine(QPointF(x, y0), QPointF(x, y1))
            x += step
        y = y0
        while y <= y1:
            pen = QPen(to_qcolor(GRID_BIG if (int(round(y / step)) % big) == 0 else GRID))
            pen.setWidthF(1.0 / self.zoom)
            p.setPen(pen)
            p.drawLine(QPointF(x0, y), QPointF(x1, y))
            y += step
        p.setPen(QPen(to_qcolor(AXIS), 1.5 / self.zoom))
        p.drawLine(QPointF(x0, 0), QPointF(x1, 0))
        p.setPen(QPen(to_qcolor(AXIS2), 1.5 / self.zoom))
        p.drawLine(QPointF(0, y0), QPointF(0, y1))

    def draw_overlay(self, p):
        w = 1.0 / self.zoom
        for n in self.scene().walk():
            if not getattr(n, 'visible', True):
                continue
            b = n.bounds()
            if b is None:
                pos = n.wpos() if hasattr(n, 'wpos') else None
                if pos is None:
                    continue
                p.setPen(QPen(to_qcolor(Color(0.7, 0.75, 0.85, 0.35)), w))
                p.drawLine(QPointF(pos.x - 6, pos.y), QPointF(pos.x + 6, pos.y))
                p.drawLine(QPointF(pos.x, pos.y - 6), QPointF(pos.x, pos.y + 6))
            else:
                pen = QPen(to_qcolor(Color(1, 1, 1, 0.08)), w)
                p.setPen(pen)
                p.setBrush(QColor(0, 0, 0, 0))
                p.drawRect(QRectF(b[0], b[1], b[2], b[3]))
        n = self.sel
        if n is None or n.dead:
            return
        b = n.bounds()
        c = to_qcolor(SEL)
        if b is None:
            pos = n.wpos()
            p.setPen(QPen(c, 1.5 * w))
            p.setBrush(QColor(0, 0, 0, 0))
            p.drawRect(QRectF(pos.x - 10, pos.y - 10, 20, 20))
            p.drawLine(QPointF(pos.x - 14, pos.y), QPointF(pos.x - 4, pos.y))
            p.drawLine(QPointF(pos.x + 4, pos.y), QPointF(pos.x + 14, pos.y))
            p.drawLine(QPointF(pos.x, pos.y - 14), QPointF(pos.x, pos.y - 4))
            p.drawLine(QPointF(pos.x, pos.y + 4), QPointF(pos.x, pos.y + 14))
            return
        pen = QPen(c, 1.5 * w)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(QColor(0, 0, 0, 0))
        p.drawRect(QRectF(b[0], b[1], b[2], b[3]))
        for hx, hy in ((b[0], b[1]), (b[0] + b[2], b[1]), (b[0], b[1] + b[3]), (b[0] + b[2], b[1] + b[3])):
            p.setPen(QPen(c, 1.5 * w))
            p.setBrush(QBrush(c))
            p.drawRect(QRectF(hx - 3 * w, hy - 3 * w, 6 * w, 6 * w))

    def draw_frame(self, p):
        sc = self.scene()
        f = QRectF(0, 0, sc.size.x, sc.size.y)
        tl = self.to_screen(f.left(), f.top())
        br = self.to_screen(f.right(), f.bottom())
        pen = QPen(to_qcolor(Color(1, 1, 1, 0.12)))
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(QColor(0, 0, 0, 0))
        p.drawRect(QRectF(tl.x, tl.y, br.x - tl.x, br.y - tl.y))
        p.setPen(QPen(to_qcolor(Color(0.6, 0.65, 0.75, 0.6))))
        p.drawText(QPointF(tl.x, tl.y - 5), '%s  %dx%d' % (sc.name, sc.size.x, sc.size.y))

    def draw_hud(self, p):
        g = self.game()
        p.setPen(QPen(QColor(120, 240, 170)))
        p.drawText(QPointF(10, 18), 'play  %d fps  %d nodes  %d calls' % (
            g.fps, len(list(self.scene().walk())), g.frame))
        if g.errors:
            p.setPen(QPen(QColor(255, 120, 120)))
            p.drawText(QPointF(10, 34), g.errors[-1][0] + ': ' + g.errors[-1][1])

    # --- мышь ---

    def mousePressEvent(self, ev):
        self.setFocus()
        pos = ev.position()
        w = self.to_world(pos.x(), pos.y())
        playing = self.win.playing
        btn = ev.button()
        if playing:
            g = self.game()
            g.input.mouse_move(pos.x(), pos.y())
            if btn == Qt.MouseButton.MiddleButton or self._space:
                self._mode = 'pan'
                self._press = Vec(pos.x(), pos.y())
            elif btn == Qt.MouseButton.LeftButton:
                g.input.clicked = True
                g.click(w.x, w.y)
            return
        if btn == Qt.MouseButton.MiddleButton or self._space:
            self._mode = 'pan'
            self._press = Vec(pos.x(), pos.y())
            return
        if btn == Qt.MouseButton.RightButton:
            self.show_menu(w)
            return
        if btn != Qt.MouseButton.LeftButton:
            return
        hit = self.scene().pick(w.x, w.y)
        if hit is not self.sel:
            self.sel = hit
            self.selected.emit(hit)
        if hit is not None:
            self._mode = 'drag'
            hp = hit.wpos() if hasattr(hit, 'wpos') else w
            self._off = hp - w
        else:
            self._mode = 'box'
            self._box = (w, w)

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        w = self.to_world(pos.x(), pos.y())
        if self.win.playing:
            self.game().input.mouse_move(pos.x(), pos.y())
            return
        if self._mode == 'pan':
            dx = (pos.x() - self._press.x()) / self.zoom
            dy = (pos.y() - self._press.y()) / self.zoom
            self.pan = self.pan - Vec(dx, dy)
            self._press = Vec(pos.x(), pos.y())
            self.update()
            return
        if self._mode == 'drag' and self.sel is not None and not self.sel.dead:
            target = w + self._off
            if self.snap:
                gs = self.scene().grid or 32
                target = Vec(round(target.x / gs) * gs, round(target.y / gs) * gs)
            self.set_node_world(self.sel, target)
            self.moved.emit(self.sel)
            self.update()
            return
        if self._mode == 'box':
            self._box = (self.to_world(self._press.x(), self._press.y()), w)
            self.update()
            return
        self.update()

    def mouseReleaseEvent(self, ev):
        if self._mode == 'drag':
            self.edited.emit()
        elif self._mode == 'box' and getattr(self, '_box', None):
            a, b = self._box
            x0, x1 = min(a.x, b.x), max(a.x, b.x)
            y0, y1 = min(a.y, b.y), max(a.y, b.y)
            best = None
            for n in self.scene().draw_order():
                bb = n.bounds()
                if bb is None:
                    continue
                if bb[0] < x1 and x0 < bb[0] + bb[2] and bb[1] < y1 and y0 < bb[1] + bb[3]:
                    best = n
            if best is not None:
                self.sel = best
                self.selected.emit(best)
        self._mode = None
        self._box = None
        self.update()

    def wheelEvent(self, ev):
        f = 1.15 if ev.angleDelta().y() > 0 else 1 / 1.15
        pos = ev.position()
        self.zoom_by(f, pos.x(), pos.y())

    def set_node_world(self, n, world):
        base = Vec(0, 0)
        if n.parent is not None and hasattr(n.parent, 'wpos'):
            base = n.parent.wpos()
        n.pos = world - base

    def show_menu(self, w):
        hit = self.scene().pick(w.x, w.y)
        m = QMenu(self)
        for t in self.win.node_types():
            m.addAction('add ' + t, lambda _c=False, tt=t: self.win.add_node(tt, w))
        if hit is not None:
            m.addSeparator()
            m.addAction('duplicate', lambda: self.win.dup_node(hit))
            m.addAction('delete', lambda: self.win.del_node(hit))
            m.addAction('bring to front', lambda: self.win.reorder(hit, 1))
            m.addAction('send to back', lambda: self.win.reorder(hit, -1))
        s = self.to_screen(w.x, w.y)
        m.exec(self.mapToGlobal(QPointF(s.x, s.y).toPoint()))

    # --- клавиатура ---

    def keyPressEvent(self, ev):
        name = key_name(ev.key(), ev.text())
        if name == 'space':
            self._space = True
        if self.win.playing:
            if name == 'escape':
                self.request.emit('stop')
                return
            self.game().key(name, True)
            return
        step = self.scene().grid or 32
        if ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            step = 1
        if name in ('up', 'down', 'left', 'right') and self.sel is not None:
            d = {'up': Vec(0, -step), 'down': Vec(0, step), 'left': Vec(-step, 0), 'right': Vec(step, 0)}[name]
            self.set_node_world(self.sel, self.sel.wpos() + d)
            self.moved.emit(self.sel)
            self.edited.emit()
            self.update()
            return
        if name == 'delete':
            self.request.emit('delete')
            return
        if name == 'f':
            self.frame_node(self.sel)
            return
        if name == 'f5':
            self.request.emit('play')
            return
        if name == 'd' and ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.request.emit('frame_all')
            return
        if name == 'a' and ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.request.emit('select_all')
            return

    def keyReleaseEvent(self, ev):
        name = key_name(ev.key(), ev.text())
        if name == 'space':
            self._space = False
        if self.win.playing:
            self.game().key(name, False)
