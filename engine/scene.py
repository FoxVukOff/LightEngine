from .mathx import Color, Vec
from .node import Node, Node2D, Rect, Label, Area, Light2D, Camera2D, Circle, make_node

STARTER_SCRIPT = '''# игрок: стрелки или wasd, пробел - прыжок
on_start:
    self.say("player ready")

on_update(dt):
    let dir = input.axis()
    self.vel = dir * 320
    if input.pressed("space"):
        self.vel.y = -430
    if dir:
        self.angle = lerp_angle(self.angle, dir.angle(), 0.25)
        self.flip_x = dir.x < 0
    if self.pos.y > 420:
        self.pos.y = 420
        self.vel.y = 0
'''


class Scene:
    def __init__(self, name='scene'):
        self.name = name
        self.nodes = []
        self.bg = Color(0.086, 0.094, 0.125, 1.0)
        self.grid = 32
        self.show_grid = True
        self.size = Vec(1280, 720)
        self.time = 0.0

    def add(self, node, parent=None):
        if parent is None:
            self.nodes.append(node)
            return node
        return parent.add(node)

    def remove(self, node):
        if node in self.nodes:
            self.nodes.remove(node)
            return
        if node.parent is not None:
            node.parent.remove(node)

    def clear(self):
        self.nodes = []

    def walk(self):
        for n in list(self.nodes):
            for x in n.walk():
                yield x

    def draw_order(self):
        flat = [(n, n.depth()) for n in self.walk()]
        flat.sort(key=lambda t: (t[0].z if isinstance(t[0], Node2D) else 0, t[1]))
        return [t[0] for t in flat]

    def find(self, name):
        for n in self.walk():
            if n.name == name:
                return n
        return None

    def of_type(self, t):
        return [n for n in self.walk() if n.TYPE == t]

    def camera(self):
        for n in self.of_type('Camera2D'):
            if n.active:
                return n
        return None

    def pick(self, x, y):
        best = None
        best_z = -1e9
        for n in self.draw_order():
            if not getattr(n, 'visible', True):
                continue
            if n.contains(x, y):
                z = n.z if isinstance(n, Node2D) else 0
                if z >= best_z:
                    best, best_z = n, z
        return best

    def clear_dead(self):
        for n in list(self.walk()):
            if not n.dead:
                continue
            for child in list(n.children):
                n.remove(child)
            self.remove(n)

    def build_starter(self):
        label = self.add(Label('hint'))
        label.pos = Vec(0, -220)
        label.oy = 0.0
        label.size = 16.0
        label.text = 'LightEngine - стрелки движение, пробел прыжок, F5 play'
        label.color = Color(0.6, 0.65, 0.75, 1.0)

        ground = self.add(Rect('ground'))
        ground.pos = Vec(0, 480)
        ground.w, ground.h = 1600, 80
        ground.oy = 0.0
        ground.color = Color(0.18, 0.2, 0.27, 1.0)
        ground.z = -1

        for i, x in enumerate((-220, 0, 240)):
            box = self.add(Rect('box%d' % (i + 1)))
            box.pos = Vec(x, 380)
            box.w, box.h = 56, 96
            box.oy = 1.0
            box.color = Color(0.3, 0.36, 0.48, 1.0)

        ball = self.add(Circle('ball'))
        ball.pos = Vec(420, 120)
        ball.r = 28
        ball.vel = Vec(-60, 0)
        ball.gravity = Vec(0, 900)
        ball.z = 1
        ball.script = '''# простое физическое тело
on_update(dt):
    self.angle = self.angle + 90 * dt
    if self.pos.y > 452:
        self.pos.y = 452
        self.vel.y = self.vel.y * -0.7
        self.vel.x = self.vel.x * 0.98
        if abs(self.vel.y) < 40:
            self.vel.y = 0
'''

        player = self.add(Area('player'))
        player.pos = Vec(-420, 300)
        player.w, player.h = 40, 60
        player.z = 2
        player.script = STARTER_SCRIPT

        body = player.add(Rect('body'))
        body.w, body.h = 40, 60
        body.color = Color(0.36, 0.78, 0.98, 1.0)

        lamp = player.add(Light2D('lamp'))
        lamp.pos = Vec(0, -40)
        lamp.r = 240

        cam = self.add(Camera2D('camera'))
        cam.follow = 'player'
        cam.zoom = 1.0
        cam.smooth = 0.1
        cam.z = 9
        return self
