from PyQt6.QtGui import QPainter

from .graphics import Graphics, to_qcolor
from .input import Input
from .mathx import Color, Vec, clamp, rect_overlap
from .nodescript import Ctx, NodeScript, ScriptHost


def is_ancestor(a, b):
    p = b.parent
    while p is not None:
        if p is a:
            return True
        p = p.parent
    return False


class Game(ScriptHost):
    def __init__(self, scene, res):
        ScriptHost.__init__(self, scene, res)
        self.input = Input()
        self.game = self
        self.ctx = Ctx(self)
        self.running = False
        self.fps = 0.0
        self.errors = []
        self.size = Vec(1280, 720)
        self._fps_t = 0.0
        self._fps_n = 0

    def script_of(self, n):
        if n.rt is None:
            n.rt = NodeScript(n, self.ctx)
        n.rt.sync(n.script)
        self.report(n.name, n.rt.err)
        return n.rt

    def report(self, who, err):
        if not err:
            return
        pair = (who, err)
        if pair in self.errors:
            return
        self.errors.append(pair)
        del self.errors[:-20]

    def step(self, dt):
        self.input.begin()
        self.dt = clamp(float(dt), 0.0, 0.1)
        self.time += self.dt
        self.frame += 1
        self._fps_t += self.dt
        self._fps_n += 1
        if self._fps_t >= 0.5:
            self.fps = self._fps_n / self._fps_t
            self._fps_t = 0.0
            self._fps_n = 0
        self.update_camera(self.dt)
        for n in list(self.scene.walk()):
            if n.dead:
                continue
            if n.script.strip():
                rt = self.script_of(n)
                rt.call('on_update', [self.dt])
                self.report(n.name, rt.err)
            n.update(self.dt)
            self.run_timers(n, self.dt)
        self.collide()
        self.scene.clear_dead()
        self.input.end()

    def run_timers(self, n, dt):
        if not n.timers:
            return
        rt = n.rt
        for name, period in list(n.timers.items()):
            left = n.tleft.get(name, float(period))
            left -= dt
            if left <= 0.0:
                n.tleft[name] = float(period)
                if rt is not None:
                    rt.call('on_timer', [name])
                    self.report(n.name, rt.err)
            else:
                n.tleft[name] = left

    def collide(self):
        ns = [n for n in self.scene.walk()
              if not n.dead and n.script.strip() and n.bounds() and n.rt is not None]
        for i, a in enumerate(ns):
            ab = a.bounds()
            for b in ns[i + 1:]:
                if is_ancestor(a, b) or is_ancestor(b, a):
                    continue
                key = (id(a), id(b))
                if rect_overlap(ab, b.bounds()):
                    if key not in a._touch:
                        a._touch.add(key)
                        b._touch.add(key)
                        a.rt.call('on_collide', [b.rt.api])
                        b.rt.call('on_collide', [a.rt.api])
                        self.report(a.name, a.rt.err)
                        self.report(b.name, b.rt.err)
                elif key in a._touch:
                    a._touch.discard(key)
                    b._touch.discard(key)
                    a.rt.call('on_collide_exit', [b.rt.api])
                    b.rt.call('on_collide_exit', [a.rt.api])
                    self.report(a.name, a.rt.err)
                    self.report(b.name, b.rt.err)

    def click(self, wx, wy):
        n = self.scene.pick(wx, wy)
        while n is not None and (n.rt is None or 'on_click' not in n.rt.fns):
            n = n.parent
        if n is not None and n.rt is not None:
            n.rt.call('on_click', [Vec(wx, wy)])
            self.report(n.name, n.rt.err)

    def key(self, name, down):
        if down:
            self.input.key_down(name)
        else:
            self.input.key_up(name)
        if not down:
            return
        for n in list(self.scene.walk()):
            if n.script.strip() and n.rt is not None:
                n.rt.call('on_key', [name])
                self.report(n.name, n.rt.err)

    def update_camera(self, dt):
        cam = self.scene.camera()
        if cam is None:
            return
        if cam.follow:
            t = self.scene.find(cam.follow)
            if t is not None:
                want = t.wpos()
                if cam.smooth > 0:
                    k = 1.0 - (1.0 - cam.smooth) ** max(1.0, dt * 60.0)
                    cam.pos = cam.pos.to(want, k)
                else:
                    cam.pos = want
        self.center = cam.wpos()

    def view(self, size, view=None, use_camera=True):
        cam = self.scene.camera() if use_camera else None
        if cam is not None and cam.active:
            p = cam.wpos()
            return (p.x, p.y, cam.zoom)
        if view is not None:
            return view
        return (self.size.x / 2, self.size.y / 2, 1.0)

    def render(self, painter, size, scripts=True, view=None, use_camera=True):
        cx, cy, zoom = self.view(size, view, use_camera)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        bg = self.scene.bg if isinstance(self.scene.bg, Color) else Color(0.08, 0.09, 0.12)
        painter.fillRect(0, 0, int(size.x), int(size.y), to_qcolor(bg))
        painter.save()
        painter.translate(size.x / 2, size.y / 2)
        painter.scale(zoom, zoom)
        painter.translate(-cx, -cy)
        g = Graphics(painter, self.res)
        for n in self.scene.draw_order():
            if not getattr(n, 'visible', True):
                continue
            n.draw(g)
            if scripts and n.script.strip() and n.rt is not None:
                n.rt.call('on_draw', [g])
        painter.restore()
