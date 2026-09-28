import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import AUTHOR, ENGINE
from engine.project import Project
from engine.resources import app_root
from editor.mainwindow import open_app


def seed_project(p):
    """копируем демо-сцену и ассеты из сборки в новый проект"""
    p.make_dirs()
    src = app_root()
    bundled_scene = os.path.join(src, 'scenes', 'main.lscene')
    if os.path.isfile(bundled_scene) and not os.path.isfile(p.scene_path()):
        shutil.copyfile(bundled_scene, p.scene_path())
    bundled_assets = os.path.join(src, 'assets')
    if os.path.isdir(bundled_assets) and not os.listdir(p.assets):
        for name in os.listdir(bundled_assets):
            s = os.path.join(bundled_assets, name)
            if os.path.isfile(s):
                shutil.copyfile(s, os.path.join(p.assets, name))
    return p


def ensure_project(arg_scene=None):
    if arg_scene:
        p = Project.find_near(os.path.dirname(os.path.abspath(arg_scene)))
        if p is not None:
            return p, os.path.abspath(arg_scene)
        root = os.path.dirname(os.path.dirname(os.path.abspath(arg_scene)))
        return Project(root, os.path.basename(root)), os.path.abspath(arg_scene)
    p = Project.find_near()
    if p is not None:
        return p, None
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        name = os.path.basename(base) or 'LightEngine'
        p = seed_project(Project(base, name))
        p.save()
        return p, None
    root = app_root()
    p = Project(root, os.path.basename(root))
    p.make_dirs()
    p.save()
    return p, None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    arg_scene = args[0] if args and args[0].lower().endswith('.lscene') else None
    project, scene = ensure_project(arg_scene)
    app, win = open_app(project, scene)
    if os.environ.get('LE_SELFTEST'):
        for i in range(5):
            app.processEvents()
        win.select_node(win.scene.find('player'))
        win.play()
        for i in range(30):
            win.tick()
        win.stop()
        print('selftest: editor ok, %d nodes, errors %s' % (len(win.scene.nodes), win.game.errors or 'none'))
        return 0
    app.exec()
    return 0


if __name__ == '__main__':
    sys.exit(main())
