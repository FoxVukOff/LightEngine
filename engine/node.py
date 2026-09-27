import math

from .mathx import Color, Vec, hex_to_color, wrap_angle


def P(name, kind, default, lo=-1e9, hi=1e9, opts=None, step=1.0):
    return {'name': name, 'kind': kind, 'def': default, 'lo': lo, 'hi': hi, 'opts': opts, 'step': step}


TYPES = {}
ORDER = []

TEMPLATES = {
    'Area': 'on_start:\n    self.say("hello from %s")\n\non_update(dt):\n    pass\n',
    'Sprite': '# текстура и цвет задаются в инспекторе\non_update(dt):\n    pass\n',
    'Rect': 'on_update(dt):\n    pass\n',
    'Circle': 'on_update(dt):\n    pass\n',
}


def reg(cls):
    TYPES[cls.TYPE] = cls
    ORDER.append(cls.TYPE)
    return cls


ALIASES = {'Box2D': 'Rect', 'Rect2D': 'Rect', 'Text': 'Label', 'Text2D': 'Label',
           'Sprite2D': 'Sprite', 'Circle2D': 'Circle', 'Camera': 'Camera2D', 'Light': 'Light2D'}


def make_node(t, name=None):
    t = ALIASES.get(t, t)
    cls = TYPES.get(t)
    if cls is None:
        raise KeyError('unknown node type %r' % t)
    return cls(name or t)


@reg
class Node:
    TYPE = 'Node'
    SCHEMA = [
        P('name', 'str', 'node'),
        P('script', 'code', ''),
    ]

    def __init__(self, name='node'):
        self.name = name
        self.script = ''
        self.parent = None
        self.children = []
        self.dead = False
        self.rt = None
        self.timers = {}
        self.tleft = {}
        self._touch = set()

    def props(self):
        out = {}
        for k in reversed(type(self).mro()):
            for p in k.__dict__.get('SCHEMA', ()):
                out[p['name']] = p
        return list(out.values())

    def pdef(self, key):
        for p in self.props():
            if p['name'] == key:
                return p
        return None

    def set_prop(self, key, val):
        p = self.pdef(key)
        if p is None:
            return
        setattr(self, key, coerce(p, val))

    def get_prop(self, key):
        return getattr(self, key, None)

    def add(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def remove(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def walk(self):
        yield self
        for c in list(self.children):
            for n in c.walk():
                yield n

    def depth(self):
        d = 0
        p = self.parent
        while p is not None:
            d += 1
            p = p.parent
        return d

    def find(self, name):
        for n in self.walk():
            if n.name == name:
                return n
        return None

    def kill(self):
        self.dead = True

    def update(self, dt):
        pass

    def draw(self, g):
        pass

    def bounds(self):
        return None

    def contains(self, x, y):
        b = self.bounds()
        if b is None:
            return False
        return b[0] <= x <= b[0] + b[2] and b[1] <= y <= b[1] + b[3]

    def to_dict(self):
        d = {'type': self.TYPE, 'name': self.name, 'script': self.script}
        for p in self.props():
            n = p['name']
            if n in ('name', 'script'):
                continue
            v = getattr(self, n, None)
            if p['kind'] == 'vec2':
                d[n] = [v.x, v.y]
            elif p['kind'] == 'color':
                d[n] = v.to_hex()
            elif p['kind'] == 'bool':
                d[n] = bool(v)
            elif p['kind'] == 'int':
                d[n] = int(v)
            elif p['kind'] == 'float':
                d[n] = round(float(v), 4)
            else:
                d[n] = v
        d['children'] = [c.to_dict() for c in self.children]
        return d

    def copy_into(self, other):
        other.script = self.script
        for p in self.props():
            n = p['name']
            if n in ('name',):
                continue
            v = getattr(self, n, None)
            if p['kind'] == 'vec2':
                setattr(other, n, v.copy())
            elif p['kind'] == 'color':
                setattr(other, n, v.copy())
            else:
                setattr(other, n, v)
        for c in self.children:
            other.add(c.dup())
        return other

    def dup(self, name=None):
        n = make_node(self.TYPE)
        self.copy_into(n)
        n.name = name or (self.name + '_copy')
        return n

    def __repr__(self):
        return '<%s %s>' % (self.TYPE, self.name)


def coerce(p, val):
    k = p['kind']
    if k == 'vec2':
        if isinstance(val, Vec):
            return val
        return Vec(val[0], val[1])
    if k == 'color':
        if isinstance(val, Color):
            return val
        if isinstance(val, str):
            return hex_to_color(val)
        return Color(*val)
    if k == 'bool':
        return bool(val)
    if k == 'int':
        return int(val)
    if k == 'float':
        return float(val)
    if k == 'enum':
        return val if val in (p['opts'] or ()) else (p['opts'] or [val])[0]
    return str(val)


@reg
class Node2D(Node):
    TYPE = 'Node2D'
    SCHEMA = [
        P('pos', 'vec2', Vec(0, 0)),
        P('vel', 'vec2', Vec(0, 0)),
        P('gravity', 'vec2', Vec(0, 0)),
        P('angle', 'float', 0.0, -100000, 100000, step=1.0),
        P('spin', 'float', 0.0, -100000, 100000),
        P('scale', 'float', 1.0, 0.0, 64.0),
        P('z', 'int', 0, -10000, 10000),
        P('visible', 'bool', True),
    ]

    def __init__(self, name='node2d'):
        Node.__init__(self, name)
        self.pos = Vec(0, 0)
        self.vel = Vec(0, 0)
        self.gravity = Vec(0, 0)
        self.angle = 0.0
        self.spin = 0.0
        self.scale = 1.0
        self.z = 0
        self.visible = True

    def update(self, dt):
        self.pos = self.pos + (self.vel + self.gravity) * dt
        if self.spin:
            self.angle = wrap_angle(self.angle + self.spin * dt)
        if self.vel.x or self.vel.y:
            if not self.angle:
                self.angle = wrap_angle(self.vel.angle())

    def wpos(self):
        p = self.parent
        if p is None or not isinstance(p, Node2D):
            return self.pos
        return p.wpos() + self.pos * p.scale

    def wangle(self):
        p = self.parent
        return (p.wangle() if isinstance(p, Node2D) else 0.0) + self.angle

    def wscale(self):
        p = self.parent
        return (p.wscale() if isinstance(p, Node2D) else 1.0) * self.scale

    def draw(self, g):
        pass


@reg
class Sprite(Node2D):
    TYPE = 'Sprite'
    SCHEMA = [
        P('texture', 'str', ''),
        P('color', 'color', Color(1, 1, 1, 1)),
        P('w', 'float', 0.0, 0.0, 8192),
        P('h', 'float', 0.0, 0.0, 8192),
        P('ox', 'float', 0.5, 0.0, 1.0),
        P('oy', 'float', 0.5, 0.0, 1.0),
        P('flip_x', 'bool', False),
    ]

    def __init__(self, name='sprite'):
        Node2D.__init__(self, name)
        self.texture = ''
        self.color = Color(1, 1, 1, 1)
        self.w = 0.0
        self.h = 0.0
        self.ox = 0.5
        self.oy = 0.5
        self.flip_x = False
        self._tw, self._th = 64.0, 64.0

    def size(self, res):
        if self.w and self.h:
            return Vec(self.w, self.h)
        pm = res.image(self.texture) if self.texture else None
        if pm is None:
            return Vec(self._tw, self._th)
        self._tw, self._th = float(pm.width()), float(pm.height())
        s = self.scale
        return Vec((self.w or self._tw) * s, (self.h or self._th) * s)

    def draw(self, g):
        if not self.texture:
            s = self.size(g.res)
            g.rect(self.wpos().x, self.wpos().y, s.x, s.y, Color(0.3, 0.32, 0.4, 0.5), True, ox=self.ox, oy=self.oy)
            return
        s = self.size(g.res)
        w = -s.x if self.flip_x else s.x
        g.sprite(self.texture, self.wpos().x, self.wpos().y, abs(w), s.y,
                 self.color if self.color != Color(1, 1, 1, 1) else None,
                 self.wangle(), self.ox, self.oy, self.color.a)

    def bounds(self):
        s = self.size(_dummy_res)
        p = self.wpos()
        return (p.x - s.x * self.ox, p.y - s.y * self.oy, s.x, s.y)


@reg
class Rect(Node2D):
    TYPE = 'Rect'
    SCHEMA = [
        P('w', 'float', 64.0, 0.0, 100000),
        P('h', 'float', 64.0, 0.0, 100000),
        P('color', 'color', Color(0.35, 0.55, 0.95, 1.0)),
        P('filled', 'bool', True),
        P('border', 'float', 0.0, 0.0, 64.0),
        P('ox', 'float', 0.5, 0.0, 1.0),
        P('oy', 'float', 0.5, 0.0, 1.0),
    ]

    def __init__(self, name='rect'):
        Node2D.__init__(self, name)
        self.w = 64.0
        self.h = 64.0
        self.color = Color(0.35, 0.55, 0.95, 1.0)
        self.filled = True
        self.border = 0.0
        self.ox = 0.5
        self.oy = 0.5

    def draw(self, g):
        s = self.wscale()
        w, h = self.w * s, self.h * s
        p, c = self.wpos(), self.color
        if self.filled and self.border > 0:
            g.rect(p.x, p.y, w, h, c, True, ox=self.ox, oy=self.oy)
            g.rect(p.x, p.y, w - self.border * 2, h - self.border * 2, Color(0, 0, 0, 0.35), True, ox=self.ox, oy=self.oy)
            return
        g.rect(p.x, p.y, w, h, c, self.filled, max(1.0, self.border), ox=self.ox, oy=self.oy)

    def bounds(self):
        s = self.wscale()
        w, h = self.w * s, self.h * s
        p = self.wpos()
        return (p.x - w * self.ox, p.y - h * self.oy, w, h)


@reg
class Circle(Node2D):
    TYPE = 'Circle'
    SCHEMA = [
        P('r', 'float', 24.0, 0.0, 100000),
        P('color', 'color', Color(0.95, 0.5, 0.3, 1.0)),
        P('filled', 'bool', True),
        P('border', 'float', 0.0, 0.0, 64.0),
    ]

    def __init__(self, name='circle'):
        Node2D.__init__(self, name)
        self.r = 24.0
        self.color = Color(0.95, 0.5, 0.3, 1.0)
        self.filled = True
        self.border = 0.0

    def draw(self, g):
        r = self.r * self.wscale()
        p, c = self.wpos(), self.color
        if self.filled and self.border > 0:
            g.circle(p.x, p.y, r, c, True)
            g.circle(p.x, p.y, max(1.0, r - self.border), Color(0, 0, 0, 0.35), True)
            return
        g.circle(p.x, p.y, r, c, self.filled, max(1.0, self.border))

    def bounds(self):
        r = self.r * self.wscale()
        p = self.wpos()
        return (p.x - r, p.y - r, r * 2, r * 2)


@reg
class Label(Node2D):
    TYPE = 'Label'
    SCHEMA = [
        P('text', 'str', 'text'),
        P('color', 'color', Color(0.92, 0.93, 0.96, 1.0)),
        P('size', 'float', 18.0, 1.0, 512.0),
        P('ox', 'float', 0.5, 0.0, 1.0),
        P('oy', 'float', 0.5, 0.0, 1.0),
    ]

    def __init__(self, name='label'):
        Node2D.__init__(self, name)
        self.text = 'text'
        self.color = Color(0.92, 0.93, 0.96, 1.0)
        self.size = 18.0
        self.ox = 0.5
        self.oy = 0.5

    def draw(self, g):
        p = self.wpos()
        g.text(p.x, p.y, self.text, self.color, self.size * self.wscale(), ox=self.ox, oy=self.oy)


@reg
class Area(Node2D):
    TYPE = 'Area'
    SCHEMA = [
        P('w', 'float', 48.0, 0.0, 100000),
        P('h', 'float', 48.0, 0.0, 100000),
        P('debug', 'bool', True),
        P('color', 'color', Color(0.3, 0.9, 0.6, 0.5)),
    ]

    def __init__(self, name='area'):
        Node2D.__init__(self, name)
        self.w = 48.0
        self.h = 48.0
        self.debug = True
        self.color = Color(0.3, 0.9, 0.6, 0.5)

    def draw(self, g):
        if self.debug:
            s = self.wscale()
            w, h = self.w * s, self.h * s
            p = self.wpos()
            g.rect(p.x, p.y, w, h, self.color, False, 1.0, ox=0.5, oy=0.5)
            g.line(p.x - 4, p.y, p.x + 4, p.y, self.color, 1.0)
            g.line(p.x, p.y - 4, p.x, p.y + 4, self.color, 1.0)

    def bounds(self):
        s = self.wscale()
        w, h = self.w * s, self.h * s
        p = self.wpos()
        return (p.x - w / 2, p.y - h / 2, w, h)


@reg
class Camera2D(Node2D):
    TYPE = 'Camera2D'
    SCHEMA = [
        P('zoom', 'float', 1.0, 0.05, 20.0),
        P('follow', 'str', ''),
        P('smooth', 'float', 0.0, 0.0, 1.0),
        P('active', 'bool', True),
    ]

    def __init__(self, name='camera'):
        Node2D.__init__(self, name)
        self.zoom = 1.0
        self.follow = ''
        self.smooth = 0.0
        self.active = True

    def draw(self, g):
        b = self.bounds()
        if b is None:
            return
        c = Color(0.95, 0.85, 0.3, 0.8)
        p = self.wpos()
        g.rect(p.x, p.y, 8, 8, c, False, 1.0)
        g.line(p.x - 12, p.y, p.x + 12, p.y, c, 1.0)
        g.line(p.x, p.y - 12, p.x, p.y + 12, c, 1.0)

    def bounds(self):
        return (0, 0, 16, 16)


@reg
class Light2D(Node2D):
    TYPE = 'Light2D'
    SCHEMA = [
        P('r', 'float', 160.0, 1.0, 100000),
        P('color', 'color', Color(1.0, 0.86, 0.6, 1.0)),
        P('power', 'float', 1.0, 0.0, 8.0),
    ]

    def __init__(self, name='light'):
        Node2D.__init__(self, name)
        self.r = 160.0
        self.color = Color(1.0, 0.86, 0.6, 1.0)
        self.power = 1.0

    def draw(self, g):
        p = self.wpos()
        g.glow(p.x, p.y, self.r * self.wscale(), self.color, self.power)


class _DummyRes:
    def image(self, name):
        return None


_dummy_res = _DummyRes()
