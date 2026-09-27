import os
import random
import sys

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QSoundEffect

IMG_EXT = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.svg')
SND_EXT = ('.wav', '.ogg', '.mp3', '.flac')


def app_root():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Resources:
    def __init__(self, root=None):
        self.root = root or app_root()
        self.dirs = [os.path.join(self.root, 'assets'), os.path.join(os.getcwd(), 'assets')]
        self.pix = {}
        self.tint = {}
        self.snd = {}
        self.missing_names = set()

    def find(self, name, exts=IMG_EXT):
        if not name:
            return None
        rel = str(name).replace('\\', '/')
        if not rel.lower().endswith(tuple(exts)):
            base = os.path.splitext(rel)[0]
            for e in exts:
                for d in self.dirs:
                    p = os.path.join(d, base + e)
                    if os.path.isfile(p):
                        return p
            return None
        for d in self.dirs:
            p = os.path.join(d, rel)
            if os.path.isfile(p):
                return p
        return None

    def image(self, name):
        p = self.find(name)
        if p is None:
            self.missing(name)
            return None
        if p not in self.pix:
            pm = QPixmap(p)
            if pm.isNull():
                self.missing(name)
                return None
            self.pix[p] = pm
        return self.pix[p]

    def tinted(self, name, color):
        pm = self.image(name)
        if pm is None:
            return None
        key = (pm.cacheKey(), color.to_hex())
        if key not in self.tint:
            from PyQt6.QtGui import QPainter
            cp = QPixmap(pm)
            p = QPainter(cp)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(cp.rect(), color)
            p.end()
            self.tint[key] = cp
        return self.tint[key]

    def sound(self, name):
        p = self.find(name, SND_EXT)
        if p is None:
            self.missing(name)
            return None
        if p not in self.snd:
            from PyQt6.QtWidgets import QApplication
            qapp = QApplication.instance()
            if qapp is None:
                return None
            fx = QSoundEffect(qapp)
            fx.setSource(QUrl.fromLocalFile(p))
            self.snd[p] = fx
        return self.snd[p]

    def missing(self, name):
        if name in self.missing_names:
            return
        self.missing_names.add(name)
        print('[res] not found: %s (assets)' % name)

    def list_assets(self):
        out = {'img': [], 'snd': []}
        seen = set()
        for d in self.dirs:
            if not os.path.isdir(d):
                continue
            for base, _dirs, files in os.walk(d):
                for f in files:
                    p = os.path.join(base, f)
                    rel = os.path.relpath(p, d).replace('\\', '/')
                    if rel in seen:
                        continue
                    seen.add(rel)
                    if rel.lower().endswith(IMG_EXT):
                        out['img'].append(rel)
                    elif rel.lower().endswith(SND_EXT):
                        out['snd'].append(rel)
        return out
