"""сборка игры из проекта в отдельный exe"""

import os
import shutil
import sys

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build.pack import engine_root, have_pyinstaller, run_pyinstaller

STUB = '''import sys
from engine.gameapp import main

if __name__ == '__main__':
    sys.exit(main())
'''


def build(project, name='game', entry=None, console=False, icon=None):
    if not have_pyinstaller():
        raise RuntimeError('pyinstaller not found, run: pip install pyinstaller')
    root = engine_root()
    entry = entry or project.scene_path()
    if not os.path.isfile(entry):
        raise RuntimeError('scene not found: %s' % entry)
    out = os.path.join(project.dist, '.build_%s' % name)
    if os.path.isdir(out):
        shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    stub = os.path.join(out, 'game_entry.py')
    with open(stub, 'w', encoding='utf-8') as f:
        f.write(STUB)

    adds = [
        (os.path.join(root, 'engine'), 'engine'),
        (os.path.join(root, 'lscript'), 'lscript'),
        (project.assets, 'assets'),
        (entry, 'scenes'),
    ]
    if os.path.isdir(project.scripts):
        adds.append((project.scripts, 'scripts'))
    folder = run_pyinstaller(name, stub, out, adds=adds,
                             hidden=('engine.gameapp', 'engine.game', 'engine.nodescript',
                                     'engine.project', 'engine.serialize', 'lscript.parser',
                                     'lscript.runtime', 'lscript.builtins'),
                             console=console,
                             icon=icon or os.path.join(project.root, 'assets', 'icon.ico'))
    final = os.path.join(project.dist, name)
    if os.path.abspath(folder) != os.path.abspath(final):
        shutil.rmtree(final, ignore_errors=True)
        shutil.move(folder, final)
    shutil.rmtree(out, ignore_errors=True)
    print('[build] game ready: %s' % final)
    return final


def main():
    import argparse
    ap = argparse.ArgumentParser(description='build a lightengine game to exe')
    ap.add_argument('project', help='path to project.json or project folder')
    ap.add_argument('--name', default=None)
    ap.add_argument('--scene', default=None)
    ap.add_argument('--console', action='store_true')
    a = ap.parse_args()
    from engine.project import Project
    path = a.project
    if os.path.isdir(path):
        path = os.path.join(path, 'project.json')
    p = Project.open(path)
    name = a.name or p.name
    print(build(p, name, a.scene, console=a.console))
    return 0


if __name__ == '__main__':
    sys.exit(main())
