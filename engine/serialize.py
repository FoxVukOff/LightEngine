import json
import os

from .mathx import Color, Vec, hex_to_color
from .node import make_node, Node, Node2D
from .scene import Scene

EXT = '.lscene'


def scene_to_dict(sc):
    return {
        'format': 1,
        'name': sc.name,
        'bg': sc.bg.to_hex(),
        'grid': sc.grid,
        'show_grid': sc.show_grid,
        'size': [sc.size.x, sc.size.y],
        'nodes': [n.to_dict() for n in sc.nodes],
    }


def scene_from_dict(d):
    sc = Scene(d.get('name', 'scene'))
    sc.bg = hex_to_color(d.get('bg', '#161821'))
    sc.grid = int(d.get('grid', 32))
    sc.show_grid = bool(d.get('show_grid', True))
    sz = d.get('size', [1280, 720])
    sc.size = Vec(sz[0], sz[1])
    for nd in d.get('nodes', []):
        sc.add(node_from_dict(nd))
    return sc


def node_from_dict(d):
    n = make_node(d.get('type', 'Node2D'), d.get('name', 'node'))
    n.script = d.get('script', '')
    for p in n.props():
        key = p['name']
        if key in ('name', 'script'):
            continue
        if key not in d:
            setattr(n, key, _fresh(p))
            continue
        n.set_prop(key, d[key])
    for cd in d.get('children', []):
        n.add(node_from_dict(cd))
    return n


def _fresh(p):
    v = p['def']
    if p['kind'] == 'vec2':
        return v.copy()
    if p['kind'] == 'color':
        return v.copy()
    return v


def save_scene(path, sc):
    folder = os.path.dirname(os.path.abspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(scene_to_dict(sc), f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def load_scene(path):
    with open(path, 'r', encoding='utf-8') as f:
        return scene_from_dict(json.load(f))
