"""сборка самого движка в exe"""

import os
import sys

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build.pack import engine_root, have_pyinstaller, run_pyinstaller


def build(name='LightEngine', onefile=True, console=False, icon=None):
    if not have_pyinstaller():
        raise RuntimeError('pyinstaller not found, run: pip install pyinstaller')
    root = engine_root()
    out = os.path.join(root, 'build')
    adds = [
        (os.path.join(root, 'build'), 'build'),
        (os.path.join(root, 'assets'), 'assets'),
        (os.path.join(root, 'scenes'), 'scenes'),
        (os.path.join(root, 'examples'), 'examples'),
        (os.path.join(root, 'project.json'), '.'),
    ]
    exe = run_pyinstaller(name, os.path.join(root, 'main.py'), out, adds=adds,
                          hidden=('build.build_game', 'build.pack'),
                          onefile=onefile, console=console,
                          icon=icon or os.path.join(root, 'assets', 'icon.ico'))
    print('[build] engine ready: %s' % exe)
    return exe


def main():
    import argparse
    ap = argparse.ArgumentParser(description='build lightengine to exe')
    ap.add_argument('--name', default='LightEngine')
    ap.add_argument('--onedir', action='store_true', help='faster start, folder with exe')
    ap.add_argument('--console', action='store_true', help='keep the console window')
    a = ap.parse_args()
    print(build(a.name, onefile=not a.onedir, console=a.console))
    return 0


if __name__ == '__main__':
    sys.exit(main())
