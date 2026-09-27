import json
import os
import shutil

from . import AUTHOR, ENGINE, LANG
from .mathx import Vec, hex_to_color

FILE = 'project.json'
DIRS = ('assets', 'scenes', 'dist', 'scripts')


def default_project(root, name='light'):
    return Project(root, name)


class Project:
    def __init__(self, root, name='light', entry='main.lscene', w=1280, h=720, bg='#161821'):
        self.root = os.path.abspath(root)
        self.name = name
        self.entry = entry
        self.w = int(w)
        self.h = int(h)
        self.bg = bg
        self.path = os.path.join(self.root, FILE)
        self.recent = []

    @property
    def assets(self):
        return os.path.join(self.root, 'assets')

    @property
    def scenes(self):
        return os.path.join(self.root, 'scenes')

    @property
    def dist(self):
        return os.path.join(self.root, 'dist')

    @property
    def scripts(self):
        return os.path.join(self.root, 'scripts')

    def scene_path(self, name=None):
        n = name or self.entry
        if not n.lower().endswith('.lscene'):
            n += '.lscene'
        return os.path.join(self.scenes, n)

    def rel(self, path):
        try:
            return os.path.relpath(path, self.root).replace('\\', '/')
        except ValueError:
            return path

    def make_dirs(self):
        for d in (self.assets, self.scenes, self.dist, self.scripts):
            os.makedirs(d, exist_ok=True)

    def to_dict(self):
        return {
            'engine': ENGINE,
            'lang': LANG,
            'author': AUTHOR,
            'name': self.name,
            'entry': self.entry,
            'size': [self.w, self.h],
            'bg': self.bg,
        }

    def save(self):
        self.make_dirs()
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return self.path

    def new_scene_file(self, name):
        p = self.scene_path(name)
        return p

    def list_scenes(self):
        if not os.path.isdir(self.scenes):
            return []
        return sorted(f for f in os.listdir(self.scenes) if f.lower().endswith('.lscene'))

    def read(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        self.name = d.get('name', self.name)
        self.entry = d.get('entry', self.entry)
        size = d.get('size', [self.w, self.h])
        self.w, self.h = int(size[0]), int(size[1])
        self.bg = d.get('bg', self.bg)
        return self

    @staticmethod
    def open(path):
        p = Project(os.path.dirname(os.path.abspath(path)))
        p.path = os.path.abspath(path)
        p.make_dirs()
        return p.read()

    @staticmethod
    def find_near(cwd=None):
        cur = os.path.abspath(cwd or os.getcwd())
        while True:
            p = os.path.join(cur, FILE)
            if os.path.isfile(p):
                return Project.open(p)
            parent = os.path.dirname(cur)
            if parent == cur:
                return None
            cur = parent

    def starter(self, scene_cls, scene_mod):
        from . import serialize
        sc = scene_cls(self.name)
        sc.size = Vec(self.w, self.h)
        sc.bg = hex_to_color(self.bg)
        sc.build_starter()
        self.make_dirs()
        p = self.scene_path(self.entry)
        serialize.save_scene(p, sc)
        return p

    def copy_into(self, dest_root, name=None):
        dest_root = os.path.abspath(dest_root)
        os.makedirs(dest_root, exist_ok=True)
        for d in ('assets', 'scenes', 'scripts'):
            src = os.path.join(self.root, d)
            dst = os.path.join(dest_root, d)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        p = Project(dest_root, name or self.name)
        p.entry = self.entry
        p.save()
        return p
