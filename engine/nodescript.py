import random

from lscript.errors import ScriptError
from lscript.builtins import make_globals
from lscript.runtime import Env, Func, Interp, to_str
from lscript.parser import parse

from .input import Input
from .mathx import Vec

HOOKS = ('on_start', 'on_update', 'on_draw', 'on_click', 'on_key', 'on_collide', 'on_collide_exit', 'on_timer')


class NullGraphics:
    res = None

    def __getattr__(self, name):
        return lambda *a, **kw: None


NULL_GFX = NullGraphics()


class NodeApi:
    __slots__ = ('n', 'ctx', 'g')

    def __init__(self, node, ctx):
        object.__setattr__(self, 'n', node)
        object.__setattr__(self, 'ctx', ctx)
        object.__setattr__(self, 'g', NULL_GFX)

    def __getattr__(self, name):
        n = self.n
        if name == 'x':
            return n.pos.x
        if name == 'y':
            return n.pos.y
        if name == 'width':
            b = n.bounds()
            return b[2] if b else 0.0
        if name == 'height':
            b = n.bounds()
            return b[3] if b else 0.0
        if name == 'alive':
            return not n.dead
        if name == 'node':
            return n
        host = self.ctx.host
        if name in ('scene', 'game', 'input', 'time', 'dt', 'frame', 'screen', 'center', 'res'):
            return getattr(host, name)
        if hasattr(n, name):
            return getattr(n, name)
        raise AttributeError('no field %r' % name)

    def __setattr__(self, name, val):
        n = self.n
        if name == 'x':
            n.pos.x = float(val)
        elif name == 'y':
            n.pos.y = float(val)
        elif name == 'alive':
            if not val:
                n.kill()
        elif n.pdef(name) is not None:
            n.set_prop(name, val)
        else:
            raise AttributeError('no field %r' % name)

    @property
    def ls_type(self):
        return self.n.TYPE

    def __repr__(self):
        return '<%s %s>' % (self.n.TYPE, self.n.name)

    # --- api ---

    def say(self, *args):
        self.ctx.log(' '.join(to_str(a) for a in args), self.n)

    def move(self, dx, dy=None):
        if dy is None:
            self.n.pos = self.n.pos + dx
        else:
            self.n.pos = self.n.pos + Vec(dx, dy)
        return self.n.pos

    def set_pos(self, x, y=None):
        self.n.pos = Vec(x) if y is None else Vec(x, y)
        return self.n.pos

    def set_vel(self, x, y=None):
        self.n.vel = Vec(x) if y is None else Vec(x, y)
        return self.n.vel

    def look_at(self, x, y=None):
        t = Vec(x) if y is None else Vec(x, y)
        self.n.angle = self.n.pos.angle_to(t)
        return self.n.angle

    def dist_to(self, other):
        o = other.n if isinstance(other, NodeApi) else other
        if hasattr(o, 'wpos'):
            o = o.wpos()
        return self.n.wpos().dist_to(o if isinstance(o, Vec) else Vec(o))

    def kill(self):
        self.n.kill()

    def clone(self, name=None):
        c = self.n.dup(name)
        if self.n.parent is not None:
            self.n.parent.add(c)
        else:
            self.ctx.host.scene.add(c)
        return NodeApi(c, self.ctx)

    def get(self, name):
        return self.ctx.host.scene.find(name)

    def find(self, name):
        for n in self.n.walk():
            if n.name == name:
                return NodeApi(n, self.ctx)
        return None

    def add(self, t, name=None):
        from .node import make_node
        child = make_node(t, name)
        self.n.add(child)
        return NodeApi(child, self.ctx)

    def count_children(self, t=None):
        return len([c for c in self.n.children if t is None or c.TYPE == t])

    def remove(self, other):
        n = other.n if isinstance(other, NodeApi) else other
        self.ctx.host.scene.remove(n)

    def play(self, name, loop=1, volume=1.0):
        self.ctx.host.play_sound(name, loop, volume)

    def timer(self, name, period):
        self.n.timers[name] = period
        return self.n

    def rect(self, *a):
        return self.g.rect(*a)

    def circle(self, *a):
        return self.g.circle(*a)

    def line(self, *a):
        return self.g.line(*a)

    def text(self, *a):
        return self.g.text(*a)

    def sprite(self, *a):
        return self.g.sprite(*a)

    def poly(self, *a):
        return self.g.poly(*a)

    def glow(self, *a):
        return self.g.glow(*a)


class Ctx:
    def __init__(self, host):
        self.host = host
        self.globals = make_globals(host)

    def log(self, msg, node=None):
        self.host.log(msg, node)


class NodeScript:
    def __init__(self, node, ctx):
        self.node = node
        self.ctx = ctx
        self.env = None
        self.interp = Interp(node.name or 'node')
        self.api = NodeApi(node, ctx)
        self.fns = {}
        self.text = None
        self.err = None

    def sync(self, text):
        if text == self.text:
            return
        self.text = text
        self.err = None
        self.fns = {}
        if not text or not text.strip():
            self.env = None
            return
        try:
            stmts = parse(text, self.node.name or 'node')
        except ScriptError as e:
            self.err = str(e)
            return
        env = Env()
        env.vars.update(self.ctx.globals)
        env.define('self', self.api)
        self.env = env
        self.interp = Interp(self.node.name or 'node')
        self.interp.run(stmts, env)
        for h in HOOKS:
            f = env.get(h)
            if isinstance(f, Func):
                self.fns[h] = f
        self.call('on_start', [])

    def call(self, name, args=(), gfx=None):
        fn = self.fns.get(name)
        if fn is None:
            return None
        if gfx is not None:
            self.api.g = gfx
        try:
            return self.interp.invoke(fn, list(args))
        except ScriptError as e:
            self.err = str(e)
            return None
        except RecursionError:
            self.err = 'stack overflow in %s' % name
            return None
        finally:
            if gfx is not None:
                self.api.g = NULL_GFX


# хост для консоли редактора, тот же интерфейс что у game
class ScriptHost:
    def __init__(self, scene, res):
        self.scene = scene
        self.res = res
        self.time = 0.0
        self.dt = 0.0
        self.frame = 0
        self.screen = Vec(1280, 720)
        self.center = Vec(640, 360)
        self.input = Input()
        self.game = None
        self.out = []

    def log(self, msg, node=None):
        self.out.append('[%s] %s' % (node.name, msg) if node else str(msg))
        if len(self.out) > 200:
            del self.out[:100]

    def rand(self, a=None, b=None):
        if a is None:
            return random.random()
        if b is None:
            return random.random() * a
        return random.uniform(a, b)

    def randi(self, a, b=None):
        if b is None:
            return random.randint(0, int(a) - 1)
        return random.randint(int(a), int(b))

    def choice(self, seq):
        return random.choice(list(seq))

    def shuffle(self, seq):
        random.shuffle(seq)
        return seq

    def chance(self, p):
        return random.random() < p

    def play_sound(self, name, loop=1, volume=1.0):
        fx = self.res.sound(name)
        if fx is not None:
            fx.setVolume(volume)
            fx.setLoopCount(loop)
            fx.play()
