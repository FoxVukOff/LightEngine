import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.mathx import Color, Vec, hex_to_color, rgb
from lscript.parser import parse
from lscript.runtime import Env, Interp, Range
from lscript.builtins import make_globals
from lscript.errors import ScriptError

fails = []


def check(name, got, want):
    ok = got == want
    print(('  ok  ' if ok else ' FAIL ') + name + ('' if ok else ' got %r want %r' % (got, want)))
    if not ok:
        fails.append(name)


class Host:
    scene = None
    game = None
    input = None
    res = None
    time = 0.0
    dt = 0.016
    frame = 1
    screen = Vec(1280, 720)
    center = Vec(640, 360)
    out = []

    def log(self, msg, node=None):
        self.out.append(msg)

    def rand(self, a=None, b=None):
        return 0.5

    def randi(self, a, b=None):
        return 1

    def choice(self, s):
        return list(s)[0]

    def shuffle(self, s):
        return s

    def chance(self, p):
        return True

    def play_sound(self, *a):
        pass


def run(src, env=None):
    e = env or Env()
    if not e.get('__host'):
        e.vars.update(make_globals(Host()))
        e.define('__host', 1)
    Interp('test').run(parse(src, 'test'), e)
    return e


print('LightScript')
e = run('''
let a = 2
let b = 3
let s = "sum=" + (a + b)
const K = 10
func add(x, y=5):
    return x + y

let r = add(a, b) + K
let lst = [1, 2, 3, 4]
let d = {"hp": 10, "name": "hero"}
let total = 0
for i in 0..4:
    total += i

let n = 0
while n < 3:
    n += 1

let p = v2(3, 4)
let ang = p.angle() |> round
let t = 7 > 3 ? "yes" : "no"
let f = a if a < b else 0
let g = null ?? 42
let h = 5 |> clamp(0, 3)
repeat 2:
    n += 10
''')
check('arithmetic', e.get('r'), 15)
check('string concat', e.get('s'), 'sum=5')
check('range sum', e.get('total'), 6)
check('while', e.get('n'), 23)
check('vec len math', e.get('ang'), 53)
check('ternary', e.get('t'), 'yes')
check('ternary if', e.get('f'), 2)
check('coalesce', e.get('g'), 42)
check('pipe clamp', e.get('h'), 3)
check('list index', e.get('lst')[2], 3)
check('dict get', e.get('d')['hp'], 10)
check('color', rgb(255, 0, 0).to_hex(), '#ff000001')
check('range obj', list(Range(0, 5, 2)), [0, 2, 4])

e3 = run('''
let d = {"hp": 10}
let hp = d.hp
let miss = d?.nope ?? -1
let deep = {"a": {"b": 7}}["a"]["b"]
let joined = keys(d)
let sorted_keys = sort(keys({"z": 1, "a": 2}))
''')
check('dict attr', e3.get('hp'), 10)
check('safe attr', e3.get('miss'), -1)
check('nested index', e3.get('deep'), 7)
check('keys', e3.get('joined'), ['hp'])
check('sort keys', e3.get('sorted_keys'), ['a', 'z'])

e2 = Env()
e2.vars.update(make_globals(Host()))
e2.define('__host', 1)
Interp('test').run(parse('''
func fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

class_free = 1
let big = fib(12)
for k, v in items({"a": 1, "b": 2}):
    pass
let sorted_list = sort([3, 1, 2])
let has_key = "hp" in {"hp": 1}
'''), e2)
check('recursion', e2.get('big'), 144)
check('sort', e2.get('sorted_list'), [1, 2, 3])
check('in dict', e2.get('has_key'), True)

try:
    run('let x = (')
    check('syntax error raises', False, True)
except ScriptError as err:
    check('syntax error raises', 'test:' in str(err), True)

try:
    run('undefined_name_xyz')
    check('unknown name raises', False, True)
except ScriptError:
    check('unknown name raises', True, True)

print('engine')
from engine.scene import Scene
from engine.serialize import load_scene, save_scene, scene_to_dict, scene_from_dict
from engine.node import make_node, ORDER

sc = Scene('demo')
sc.build_starter()
check('starter nodes', len(list(sc.walk())) > 6, True)
check('types registry', 'Sprite' in ORDER and 'Area' in ORDER, True)

d = scene_to_dict(sc)
sc2 = scene_from_dict(d)
check('scene roundtrip', len(sc2.nodes), len(sc.nodes))
check('script roundtrip', sc2.find('player').script.count('\n'), sc.find('player').script.count('\n'))
check('child pos local', sc2.find('body').pos, Vec(0, 0))
check('wpos child', sc2.find('lamp').wpos(), sc2.find('player').pos + Vec(0, -40))

tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp.lscene')
save_scene(tmp, sc)
sc3 = load_scene(tmp)
os.remove(tmp)
check('file roundtrip', sc3.find('player').pos, sc.find('player').pos)

n = make_node('Rect', 'r1')
n.set_prop('w', 32)
n.set_prop('color', '#ff0000')
check('coerce float', n.w, 32.0)
check('coerce color', n.color, Color(1, 0, 0, 1))
check('coerce vec', n.set_prop('pos', [3, 4]) or n.pos, Vec(3, 4))
d2 = n.to_dict()
check('node dict color', d2['color'], '#ff0000ff')
check('node dict vec', d2['pos'], [3.0, 4.0])

print('game')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication
from engine.game import Game
from engine.resources import Resources
from engine.node import Rect, Area, Node2D

app = QApplication.instance() or QApplication([])
sc4 = Scene('t')
a = sc4.add(Rect('ground'))
a.pos = Vec(0, 0)
a.w, a.h = 100, 20
b = sc4.add(Area('box'))
b.script = 'on_update(dt):\n    self.pos.y = self.pos.y + 10 * dt\n'
g = Game(sc4, Resources(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for i in range(10):
    g.step(0.016)
check('node moved by script', round(b.pos.y, 3), 1.6)
check('no script errors', g.errors, [])

g2 = Game(sc4, Resources())
g2.input.key_down('right')
g2.step(0.016)
check('input axis', g2.input.axis(), Vec(1, 0))
g2.key('x', True)
g2.key('x', False)
check('key hook state', 'x' in g2.input.held, False)

img = QImage(320, 200, QImage.Format.Format_ARGB32)
p = QPainter(img)
g2.render(p, Vec(320, 200))
p.end()
check('render wrote pixels', img.pixelColor(160, 100).alpha() > 0, True)

g3 = Game(Scene('empty'), Resources())
g3.step(0.016)
img2 = QImage(64, 64, QImage.Format.Format_ARGB32)
p2 = QPainter(img2)
g3.render(p2, Vec(64, 64))
p2.end()
bg = g3.scene.bg
px = img2.pixelColor(5, 5)
check('empty scene render', (px.red(), px.green(), px.blue()),
      (round(bg.r * 255), round(bg.g * 255), round(bg.b * 255)))

print('examples')
import glob
from lscript.errors import ScriptError as _SE
ex_files = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples', '*.ls')))
for f in ex_files:
    name = os.path.basename(f)
    try:
        from lscript.parser import parse as _parse
        _parse(open(f, encoding='utf-8').read(), name)
        check('parse ' + name, True, True)
    except _SE as err:
        check('parse ' + name, str(err), True)

print('examples run')
from engine.node import Area
from engine.mathx import Vec
ex_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples')
for fn in ('follow_mouse.ls', 'spawner.ls', 'on_draw.ls'):
    scx = Scene('ex')
    player = scx.add(Area('player'))
    player.pos = Vec(0, 0)
    node = scx.add(Area('main'))
    node.pos = Vec(300, 0)
    node.w, node.h = 60, 60
    with open(os.path.join(ex_dir, fn), encoding='utf-8') as f:
        node.script = f.read()
    gx = Game(scx, Resources())
    gx.input.mouse_move(120, 90)
    gx.key('left', True)
    for i in range(150):
        gx.step(0.016)
    check('example runs ' + fn, gx.errors, [])
    if fn == 'spawner.ls':
        spawned = len(node.children)
check('spawner made enemies', spawned > 0, True)

print()
if fails:
    print('%d failed: %s' % (len(fails), ', '.join(fails)))
    sys.exit(1)
print('all ok')