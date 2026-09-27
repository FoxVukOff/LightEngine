import os
import sys
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QApplication, QWidget

from . import ENGINE
from .game import Game
from .input import key_name
from .mathx import Vec
from .resources import Resources
from .scene import Scene
from .serialize import load_scene


class GameWindow(QWidget):
    def __init__(self, game, title='LightEngine'):
        QWidget.__init__(self)
        self.game = game
        self.last = time.perf_counter()
        self.setWindowTitle(title)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.resize(int(game.size.x), int(game.size.y))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(15)

    def tick(self):
        now = time.perf_counter()
        dt = now - self.last
        self.last = now
        self.game.step(dt)
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        sz = Vec(self.width(), self.height())
        self.game.size = sz
        self.game.render(p, sz)
        p.setPen(Qt.GlobalColor.white)
        p.drawText(8, 16, '%s  %d fps  %d nodes' % (self.game.scene.name, self.game.fps,
                                                      len(list(self.game.scene.walk()))))

    def keyPressEvent(self, ev):
        k = key_name(ev.key(), ev.text())
        self.game.key(k, True)
        if k == 'escape':
            self.close()

    def keyReleaseEvent(self, ev):
        self.game.key(key_name(ev.key(), ev.text()), False)

    def mouseMoveEvent(self, ev):
        self.game.input.mouse_move(ev.position().x(), ev.position().y())

    def mousePressEvent(self, ev):
        self.game.input.mouse_move(ev.position().x(), ev.position().y())
        self.game.input.buttons.add(ev.button())
        if ev.button() == Qt.MouseButton.LeftButton:
            self.game.input.clicked = True
            self.game.click(ev.position().x(), ev.position().y())

    def mouseReleaseEvent(self, ev):
        self.game.input.buttons.discard(ev.button())

    def wheelEvent(self, ev):
        self.game.input.wheel = ev.angleDelta().y() / 120.0

    def closeEvent(self, ev):
        self.timer.stop()


def make_game(scene, root=None):
    res = Resources(root)
    return Game(scene, res)


def run_scene(scene, root=None, title=ENGINE):
    app = QApplication.instance() or QApplication(sys.argv)
    g = make_game(scene, root)
    w = GameWindow(g, title)
    w.show()
    app.exec()
    return 0


def find_scene(root):
    proj_scene = os.path.join(root, 'scenes', 'main.lscene')
    if os.path.isfile(proj_scene):
        return proj_scene
    if os.path.isfile(root) and root.lower().endswith('.lscene'):
        return root
    for base in (root, os.getcwd()):
        d = os.path.join(base, 'scenes')
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith('.lscene'):
                    return os.path.join(d, f)
    return None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = os.getcwd()
    if getattr(sys, 'frozen', False):
        root = getattr(sys, '_MEIPASS', root)
    path = next((a for a in argv if a.lower().endswith('.lscene')), None) or find_scene(root)
    if not path or not os.path.isfile(path):
        print('no scene found, pass a path to .lscene')
        dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        scenes = [f for f in os.listdir(root) if f.endswith('.lscene')]
        print('dirs: %s' % ', '.join(sorted(dirs)))
        print('scenes here: %s' % ', '.join(scenes))
        sd = os.path.join(root, 'scenes')
        if os.path.isdir(sd):
            print('scenes dir: %s' % ', '.join(sorted(os.listdir(sd))))
        return 1
    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    scene = load_scene(path)
    return run_scene(scene, proj_root, scene.name)
