"""папка проекта: project.json плюс свои assets, scenes и dist"""

import json
import os

from . import AUTHOR, ENGINE, LANG

FILE = 'project.json'
DIRS = ('assets', 'scenes', 'dist', 'scripts')


class Project:
    def __init__(self, root, name='light', entry='main.lscene', w=1280, h=720, bg='#161821'):
        self.root = os.path.abspath(root)
        self.name = name
        self.entry = entry
        self.w = int(w)
        self.h = int(h)
        self.bg = bg
        self.path = os.path.join(self.root, FILE)

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
