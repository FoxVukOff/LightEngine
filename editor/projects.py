import os
import re
import shutil

from engine.project import Project
from engine.resources import app_root
from engine.scene import Scene
from engine.serialize import load_scene, save_scene

SAFE = re.compile(r'[^A-Za-z0-9_\- ]+')


def engine_dir():
    if getattr(__import__('sys'), 'frozen', False):
        return os.path.dirname(__import__('sys').executable)
    return app_root()


def projects_dir():
    return os.path.join(engine_dir(), 'projects')


def clean_name(name):
    return SAFE.sub('', str(name or '')).strip().replace(' ', '_') or 'game'


def list_projects(d=None):
    d = d or projects_dir()
    out = []
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f, 'project.json')
        if os.path.isfile(p):
            out.append(Project.open(p))
    return out


def create_project(name, d=None, starter=True):
    d = d or projects_dir()
    name = clean_name(name)
    root = os.path.join(d, name)
    if os.path.isfile(os.path.join(root, 'project.json')):
        raise FileExistsError('project %s already exists' % name)
    p = Project(root, name)
    p.make_dirs()
    p.save()
    if starter:
        make_starter(p)
    return p


def make_starter(p):
    tmpl = os.path.join(app_root(), 'scenes', 'main.lscene')
    target = p.scene_path(p.entry)
    if os.path.isfile(tmpl) and os.path.abspath(tmpl) != os.path.abspath(target):
        shutil.copyfile(tmpl, target)
        return load_scene(target)
    sc = Scene(p.name)
    sc.build_starter()
    save_scene(target, sc)
    return sc


def remember(p):
    d = projects_dir()
    if p is None or not os.path.isdir(d):
        return
    try:
        with open(os.path.join(d, 'last.txt'), 'w', encoding='utf-8') as f:
            f.write(os.path.abspath(p.path))
    except OSError:
        pass


def last():
    f = os.path.join(projects_dir(), 'last.txt')
    if os.path.isfile(f):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                path = fh.read().strip()
            if os.path.isfile(path):
                return Project.open(path)
        except (OSError, ValueError):
            pass
    return None
