import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import AUTHOR, ENGINE
from engine.project import Project
from engine.resources import app_root
from editor.mainwindow import open_app


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
    app.exec()
    return 0


if __name__ == '__main__':
    sys.exit(main())
