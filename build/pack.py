import os
import shutil
import subprocess
import sys


def engine_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def python_exe():
    if getattr(sys, 'frozen', False):
        return shutil.which('python') or shutil.which('py') or 'python'
    return sys.executable


def have_pyinstaller():
    exe = python_exe()
    p = subprocess.run([exe, '-c', 'import PyInstaller'], capture_output=True)
    return p.returncode == 0


def add_arg(args, src, dst):
    if not os.path.exists(src):
        return
    args += ['--add-data', '%s%s%s' % (src, os.pathsep, dst.replace('\\', '/'))]


def run_pyinstaller(name, entry, out_dir, adds=(), hidden=(), onefile=True, console=False, icon=None):
    args = [python_exe(), '-m', 'PyInstaller', '--noconfirm', '--clean',
            '--onefile' if onefile else '--onedir']
    if not console:
        args.append('--windowed')
    args += ['--name', name,
             '--distpath', os.path.join(out_dir, 'dist'),
             '--workpath', os.path.join(out_dir, 'work'),
             '--specpath', os.path.join(out_dir, 'spec')]
    for h in hidden:
        args += ['--hidden-import', h]
    for src, dst in adds:
        add_arg(args, src, dst)
    if icon and os.path.isfile(icon):
        args += ['--icon', icon]
    args.append(entry)
    print('[build] ' + ' '.join(args))
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (p.stdout or '')[-3000:]
    err = (p.stderr or '')[-3000:]
    if out.strip():
        print(out)
    if p.returncode != 0:
        print(err, file=sys.stderr)
        raise RuntimeError('pyinstaller failed with code %d' % p.returncode)
    exe = os.path.join(out_dir, 'dist', name + '.exe')
    if not os.path.exists(exe) and os.name == 'nt':
        exe = os.path.join(out_dir, 'dist', name, name + '.exe')
    if not os.path.exists(exe):
        exe = os.path.join(out_dir, 'dist', name)
    if not os.path.exists(exe):
        raise RuntimeError('no exe at %s' % os.path.join(out_dir, 'dist', name))
    return exe
