import math


class Vec:
    __slots__ = ('x', 'y')

    def __init__(self, x=0.0, y=None):
        self.x = float(x)
        self.y = float(x) if y is None else float(y)

    def copy(self):
        return Vec(self.x, self.y)

    def set(self, x, y=None):
        self.x = float(x)
        self.y = float(x) if y is None else float(y)
        return self

    def add(self, o):
        return Vec(self.x + o.x, self.y + o.y)

    def sub(self, o):
        return Vec(self.x - o.x, self.y - o.y)

    def mul(self, s):
        if isinstance(s, Vec):
            return Vec(self.x * s.x, self.y * s.y)
        return Vec(self.x * s, self.y * s)

    def div(self, s):
        if isinstance(s, Vec):
            return Vec(self.x / s.x, self.y / s.y)
        return Vec(self.x / s, self.y / s)

    def dot(self, o):
        return self.x * o.x + self.y * o.y

    def cross(self, o):
        return self.x * o.y - self.y * o.x

    def len2(self):
        return self.x * self.x + self.y * self.y

    def len(self):
        return math.hypot(self.x, self.y)

    def normed(self):
        n = self.len()
        return Vec(self.x / n, self.y / n) if n > 1e-9 else Vec(0, 0)

    def dist_to(self, o):
        return math.hypot(self.x - o.x, self.y - o.y)

    def angle(self):
        return math.degrees(math.atan2(self.y, self.x))

    def rot(self, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return Vec(self.x * c - self.y * s, self.x * s + self.y * c)

    def angle_to(self, o):
        return math.degrees(math.atan2(o.y - self.y, o.x - self.x))

    def to(self, o, t):
        return Vec(self.x + (o.x - self.x) * t, self.y + (o.y - self.y) * t)

    def __add__(self, o):
        return Vec(self.x + o.x, self.y + o.y)

    __radd__ = __add__

    def __sub__(self, o):
        return Vec(self.x - o.x, self.y - o.y)

    def __mul__(self, s):
        return self.mul(s)

    __rmul__ = __mul__

    def __truediv__(self, s):
        return self.div(s)

    def __neg__(self):
        return Vec(-self.x, -self.y)

    def __abs__(self):
        return self.len()

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __iter__(self):
        return iter((self.x, self.y))

    def __eq__(self, o):
        return isinstance(o, Vec) and self.x == o.x and self.y == o.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __bool__(self):
        return self.x != 0.0 or self.y != 0.0

    def __repr__(self):
        return 'vec2(%.3f, %.3f)' % (self.x, self.y)


def vec2(x=0.0, y=None):
    return Vec(x, y)


class Color:
    __slots__ = ('r', 'g', 'b', 'a')

    def __init__(self, r=1.0, g=1.0, b=1.0, a=1.0):
        self.r, self.g, self.b, self.a = float(r), float(g), float(b), float(a)

    def copy(self):
        return Color(self.r, self.g, self.b, self.a)

    def with_alpha(self, a):
        return Color(self.r, self.g, self.b, a)

    def mul(self, o):
        return Color(self.r * o.r, self.g * o.g, self.b * o.b, self.a * o.a)

    def mix(self, o, t):
        return Color(self.r + (o.r - self.r) * t,
                     self.g + (o.g - self.g) * t,
                     self.b + (o.b - self.b) * t,
                     self.a + (o.a - self.a) * t)

    def to_hex(self):
        v = lambda c: max(0, min(255, int(round(c * 255))))
        return '#%02x%02x%02x%02x' % (v(self.r), v(self.g), v(self.b), v(self.a))

    def to_list(self):
        return [self.r, self.g, self.b, self.a]

    def __getitem__(self, i):
        return self.to_list()[i]

    def __iter__(self):
        return iter(self.to_list())

    def __mul__(self, o):
        if isinstance(o, Color):
            return self.mul(o)
        return Color(self.r * o, self.g * o, self.b * o)

    __rmul__ = __mul__

    def __eq__(self, o):
        return isinstance(o, Color) and self.to_list() == o.to_list()

    def __hash__(self):
        return hash(self.to_list())

    def __bool__(self):
        return self.a > 0.0

    def __repr__(self):
        return 'rgb%s' % ([int(round(c * 255)) for c in self.to_list()],)


def rgb(r, g=None, b=None, a=1.0):
    if g is None:
        n = int(r)
        return Color(((n >> 16) & 255) / 255.0, ((n >> 8) & 255) / 255.0, (n & 255) / 255.0, 1.0)
    if a is None:
        a = 1.0
    return Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)


def hex_to_color(s, a=1.0):
    s = s.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join(c * 2 for c in s)
    if len(s) not in (6, 8):
        raise ValueError('bad color %r' % s)
    n = [int(s[i:i + 2], 16) / 255.0 for i in range(0, len(s), 2)]
    while len(n) < 4:
        n.append(1.0)
    return Color(n[0], n[1], n[2], n[3] if s.startswith('#') and len(s) == 8 else a)


def color_to_hex(c):
    return c.to_hex() if isinstance(c, Color) else str(c)


def to_color(v, a=1.0):
    if isinstance(v, Color):
        return v
    if isinstance(v, str):
        return hex_to_color(v, a)
    if isinstance(v, (list, tuple)):
        if len(v) >= 4:
            return Color(v[0], v[1], v[2], v[3])
        return Color(v[0], v[1], v[2], a)
    return Color(v, v, v, a)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_angle(a, b, t):
    d = (b - a) % 360.0
    if d > 180.0:
        d -= 360.0
    return (a + d * t) % 360.0


def wrap_angle(a):
    return a % 360.0


def approach(cur, target, step):
    if cur < target:
        return min(cur + step, target)
    return max(cur - step, target)


def rect_overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
