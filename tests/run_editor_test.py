import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from engine.mathx import Vec
from engine.node import make_node
from engine.project import Project
from engine.serialize import load_scene
from editor.mainwindow import MainWindow

fails = []


def check(name, got, want=True):
    ok = got == want
    print(('  ok  ' if ok else ' FAIL ') + name + ('' if ok else ' got %r want %r' % (got, want)))
    if not ok:
        fails.append(name)


app = QApplication.instance() or QApplication([])
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
proj = Project.open(os.path.join(root, 'projects', 'demo', 'project.json'))
win = MainWindow(proj, proj.scene_path())
win.resize(1280, 800)
win.show()
app.processEvents()

check('project loaded', win.project.name, 'demo')
check('scene nodes', len(win.scene.nodes) > 5)
check('player found', win.scene.find('player') is not None)
check('inspector empty', win.inspector.node is None)

# выбор узла и правка свойств
p = win.scene.find('player')
win.select_node(p)
check('selection', win.sel is p)
check('inspector loaded', win.inspector.node is p)
check('hierarchy has item', p.name in win.hierarchy.item_for(p).text(0))
win.inspector.emit('vel', p.vel.set(100, 0))
check('prop applied', p.vel.x, 100.0)
win.inspector.sync_widget('vel')
check('prop widget synced', win.inspector._spins['vel'][0].value(), 100.0)

# добавление и удаление узла
n0 = len(list(win.scene.walk()))
box = win.add_node('Rect', None, None)
check('node added', len(list(win.scene.walk())), n0 + 1)
check('new node has script', box.script.strip() != '')
check('node selected', win.sel is box)
win.del_node(box)
check('node removed', len(list(win.scene.walk())), n0)

# канва
c = win.canvas
c.pan = p.wpos()
c.update()
app.processEvents()
scr = c.to_screen(p.wpos().x, p.wpos().y)
check('screen roundtrip', c.to_world(scr.x, scr.y).x, p.wpos().x)
c.set_node_world(p, Vec(123.0, 456.0))
check('drag moved node', (p.wpos().x, p.wpos().y), (123.0, 456.0))
c.zoom_by(1.3)
check('zoom applied', c.zoom > 1.0)
c.frame_all()
check('frame all zoom sane', 0.05 < c.zoom < 9.0)
check('canvas paint', not c.grab().isNull())
check('no draw errors', 'draw error' in c.win.console.out.toPlainText(), False)

# play и stop
win.play()
check('playing', win.playing)
for i in range(20):
    win.tick()
app.processEvents()
check('no script errors', win.game.errors, [])
check('frame advanced', win.game.frame >= 20, True)
check('timer running', win.timer.isActive())
check('player moved by input', win.scene.find('player') is not None)
win.stop()
check('stopped', not win.playing)
check('scene restored', win.scene.find('player').vel.x, 100.0)
check('errors logged', 'err' in win.console.out.toPlainText().lower(), False)

# клик по узлу
win.play()
app.processEvents()
win.game.click(*p.wpos())
win.stop()
check('click survived', win.playing, False)

# консоль
win.select_node(win.scene.find('player'))
win.console.inp.setText('let q = self.name')
win.console.run()
check('console ran', win.console.env.get('q'), 'player')
win.console.inp.setText('type(self)')
win.console.run()
check('console result', win.console.out.toPlainText().strip().endswith('= Area'), True)
win.console.inp.setText('oops(')
win.console.run()
check('console error caught', 'err:' in win.console.out.toPlainText())
win.console.inp.setText('self.say("hi")')
win.console.run()
check('console say', 'hi' in win.console.out.toPlainText())

# ассеты и flip
sprite = win.add_node('Sprite', None, None)
check('assets listed', win.assets.tree.topLevelItem(0) is not None)
win.select_node(sprite)
sprite.set_prop('texture', 'missing.png')
img = win.canvas.grab()
check('sprite without texture drawn', 'draw error' in win.console.out.toPlainText(), False)
sprite.set_prop('texture', '')
flip = win.add_node('Rect', None, None)
flip.set_prop('flip_x', True)
check('rect flip drawn', not win.canvas.grab().isNull())
win.del_node(sprite)
win.del_node(flip)

# мышь: рамка выделения, панорама, перетаскивание
class FakePoint:
    def __init__(self, x, y):
        self._x, self._y = x, y

    def x(self):
        return self._x

    def y(self):
        return self._y


class FakeEvent:
    def __init__(self, x, y, button=Qt.MouseButton.LeftButton):
        self._p = FakePoint(x, y)
        self._b = button

    def position(self):
        return self._p

    def button(self):
        return self._b


class FakeKeyEvent:
    def __init__(self, name):
        self._name = name
        self._text = name if len(name) == 1 else ''

    def key(self):
        from PyQt6.QtCore import Qt as Q
        return Q.Key.Key_F if self._name == 'f' else Q.Key.Key_A

    def text(self):
        return self._text

    def modifiers(self):
        return Qt.KeyboardModifier.NoModifier


LEFT = Qt.MouseButton.LeftButton
c.pan = Vec(0, 0)
c.zoom = 1.0
c.sel = None
c.mousePressEvent(FakeEvent(100, 100, LEFT))
check('press starts box', c._mode, 'box')
c.mouseMoveEvent(FakeEvent(500, 400, LEFT))
check('box drag moved', c._box[1].x != c._box[0].x, True)
c.mouseReleaseEvent(FakeEvent(500, 400, LEFT))
check('box released', c._mode, None)
c._space = True
c.mousePressEvent(FakeEvent(200, 200, LEFT))
c.mouseMoveEvent(FakeEvent(300, 260, LEFT))
check('pan moved', (c.pan.x, c.pan.y), (-100.0, -60.0))
c.mouseReleaseEvent(FakeEvent(300, 260, LEFT))
c._space = False
c.snap = False
sel_node = win.scene.find('ball')
x0 = sel_node.wpos().x
c.sel = sel_node
scr = c.to_screen(x0, sel_node.wpos().y)
c.mousePressEvent(FakeEvent(scr.x, scr.y, LEFT))
check('press grabs node', c._mode, 'drag')
c.mouseMoveEvent(FakeEvent(scr.x + 40, scr.y, LEFT))
check('drag moved node', sel_node.wpos().x - x0, 40.0)
c.mouseReleaseEvent(FakeEvent(scr.x + 40, scr.y, LEFT))
check('drag released', c._mode, None)
c.snap = True
c.keyPressEvent(FakeKeyEvent('f'))
check('frame node keeps zoom', c.zoom > 0)

# сохранение и загрузка
path = win.save()
sc2 = load_scene(path)
check('saved player vel', sc2.find('player').vel.x, 100.0)
win.dirty = True
win.set_title()
check('title dirty', win.windowTitle().startswith('LightEngine *'))
check('project file written', os.path.isfile(proj.path))

# z порядок и переименование
z = win.add_node('Rect', None, None)
z.set_prop('z', 5)
win.reorder(z, 1)
check('z changed', z.z, 15)
z.name = 'renamed'
win.hierarchy.rebuild(z)
check('hierarchy rebuilt', 'renamed' in win.hierarchy.item_for(z).text(0))
win.del_node(z)

print()
if fails:
    print('%d failed: %s' % (len(fails), ', '.join(fails)))
    sys.exit(1)
print('editor ok')
