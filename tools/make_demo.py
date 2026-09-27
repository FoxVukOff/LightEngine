import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.project import Project
from engine.scene import Scene
from engine.serialize import save_scene

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = Project.open(os.path.join(root, 'project.json'))
sc = Scene(p.name)
sc.build_starter()
p.make_dirs()
save_scene(p.scene_path(p.entry), sc)
print('wrote', p.scene_path(p.entry), 'nodes:', len(sc.nodes))
