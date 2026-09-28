import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('LE_SELFTEST', '1')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from engine.gameapp import main

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scene = os.path.join(root, 'projects', 'demo', 'scenes', 'main.lscene')
print('rc', main([scene]))
