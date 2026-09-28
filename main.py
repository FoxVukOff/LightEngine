import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication

from engine.project import Project
from editor import projects
from editor.crashlog import install
from editor.mainwindow import open_app
from editor.theme import apply


def pick_project(arg=None, allow_dialog=True):
    # сначала пробуем память, потом окно приветствия, ничего не создаём сами
    if arg:
        path = arg if arg.endswith('project.json') else os.path.join(arg, 'project.json')
        try:
            return Project.open(path)
        except (OSError, ValueError):
            return None
    p = projects.last()
    if p is not None:
        return p
    if not allow_dialog:
        return None
    from editor.welcome import Welcome
    dlg = Welcome()
    if dlg.exec() == Welcome.DialogCode.Accepted and dlg.picked is not None:
        return dlg.picked
    return None


def main():
    args = sys.argv[1:]
    selftest = bool(os.environ.get('LE_SELFTEST'))
    arg_scene = next((a for a in args if a.lower().endswith('.lscene')), None)
    arg_proj = None
    if '--project' in args:
        i = args.index('--project')
        if i + 1 < len(args):
            arg_proj = args[i + 1]
    else:
        arg_proj = next((a for a in args if a.endswith('.json') or os.path.isdir(a)), None)

    app = QApplication.instance() or QApplication(sys.argv)
    apply(app)
    install(projects.engine_dir())

    if selftest and arg_proj is None:
        arg_proj = os.path.join(projects.projects_dir(), 'demo')
    project = pick_project(arg_proj, allow_dialog=not selftest)
    _, win = open_app(project, arg_scene)
    if project is not None:
        projects.remember(project)
    win.show()
    if selftest:
        for i in range(5):
            app.processEvents()
        win.select_node(win.scene.find('player'))
        win.play()
        for i in range(30):
            win.tick()
        win.stop()
        print('selftest: editor ok, project %s, %d nodes, errors %s' % (
            project.name if project else 'none', len(win.scene.nodes), win.game.errors or 'none'))
        return 0
    app.exec()
    return 0


if __name__ == '__main__':
    sys.exit(main())
