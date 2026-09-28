import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtGui import QFontDatabase, QImage, QPainter
from PyQt6.QtWidgets import QApplication

from engine.mathx import Vec
from engine.project import Project
from engine.serialize import load_scene
from editor.mainwindow import MainWindow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
FONTS = (r'C:\Windows\Fonts\segoeui.ttf', r'C:\Windows\Fonts\consola.ttf',
         r'C:\Windows\Fonts\arial.ttf', r'C:\Windows\Fonts\tahoma.ttf')


def load_fonts():
    # в offscreen режиме системные шрифты не подхватываются, грузим руками
    for f in FONTS:
        if os.path.isfile(f):
            QFontDatabase.addApplicationFont(f)


def main():
    app = QApplication.instance() or QApplication([])
    load_fonts()
    os.makedirs(DOCS, exist_ok=True)
    proj = Project.open(os.path.join(ROOT, 'project.json'))
    win = MainWindow(proj, proj.scene_path())
    win.resize(1440, 860)
    win.show()
    for i in range(4):
        app.processEvents()
    win.select_node(win.scene.find('player'))
    win.canvas.frame_all()
    win.canvas.update()
    app.processEvents()
    win.grab().save(os.path.join(DOCS, 'editor.png'), 'PNG')

    scene = load_scene(proj.scene_path())
    g = win.game
    g.scene = scene
    g.size = scene.size
    for i in range(30):
        g.step(0.016)
    img = QImage(int(scene.size.x), int(scene.size.y), QImage.Format.Format_ARGB32)
    p = QPainter(img)
    g.render(p, scene.size)
    p.end()
    img.scaled(960, 540).save(os.path.join(DOCS, 'scene.png'), 'PNG')
    print('wrote docs/editor.png and docs/scene.png')


if __name__ == '__main__':
    main()
