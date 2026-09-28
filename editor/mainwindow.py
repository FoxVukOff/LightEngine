import os
import sys
import time

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (QApplication, QDockWidget, QFileDialog, QInputDialog, QLabel,
                             QMainWindow, QMenu, QMessageBox, QSizePolicy, QToolBar, QWidget)

from engine import AUTHOR, ENGINE, LANG
from engine.game import Game
from engine.mathx import Vec
from engine.node import ORDER, TEMPLATES, make_node
from engine.project import Project
from engine.resources import Resources, app_root
from engine.scene import Scene
from engine.serialize import load_scene, node_from_dict, save_scene
from editor.assets import Assets
from editor.canvas import Canvas
from editor.console import Console
from editor.hierarchy import Hierarchy
from editor.inspector import Inspector


class MainWindow(QMainWindow):
    def __init__(self, project=None, scene_path=None):
        QMainWindow.__init__(self)
        self.project = project
        self.scene_path = scene_path
        self.sel = None
        self.playing = False
        self.dirty = False
        self._snapshot = None
        self._last = time.perf_counter()
        self._last_err = None

        self.res = Resources(self.project.root if self.project else app_root())
        self.scene = Scene('main')
        self.game = Game(self.scene, self.res)
        self.game.log = self.log

        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        self.hierarchy = Hierarchy(self)
        self.inspector = Inspector(self)
        self.console = Console(self)
        self.assets = Assets(self)

        self.dock_nodes = QDockWidget('nodes', self)
        self.dock_nodes.setWidget(self.hierarchy)
        self.dock_nodes.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_nodes)

        self.dock_props = QDockWidget('properties', self)
        self.dock_props.setWidget(self.inspector)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_props)

        self.dock_assets = QDockWidget('assets', self)
        self.dock_assets.setWidget(self.assets)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_assets)

        self.dock_console = QDockWidget('console', self)
        self.dock_console.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_console)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.status = QLabel('')
        self.statusBar().addPermanentWidget(self.status)

        self.build_menus()
        self.wire()
        self.load_scene(scene_path)
        self.rebuild_ui()
        self.log('%s %s by %s, %s ready' % (ENGINE, 'prototype', AUTHOR, LANG))

    # --- сборка ui ---

    def act(self, menu, text, slot, shortcut=None, tip=''):
        a = QAction(text, self)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(shortcut)
        if tip:
            a.setStatusTip(tip)
        menu.addAction(a)
        return a

    def build_menus(self):
        mb = self.menuBar()
        m = mb.addMenu('&file')
        self.act(m, 'new scene', self.new_scene, QKeySequence('Ctrl+N'))
        self.act(m, 'open scene...', self.open_scene, QKeySequence('Ctrl+O'))
        self.act(m, 'save', self.save, QKeySequence('Ctrl+S'))
        self.act(m, 'save as...', self.save_as, QKeySequence('Ctrl+Shift+S'))
        self.act(m, 'reload from disk', self.reload)
        m.addSeparator()
        self.act(m, 'new project...', self.new_project)
        self.act(m, 'open project...', self.open_project)
        m.addSeparator()
        self.act(m, 'build game exe...', self.build_game, QKeySequence('Ctrl+B'))
        self.act(m, 'run game in window', self.run_window)
        m.addSeparator()
        self.act(m, 'quit', self.close, QKeySequence('Ctrl+Q'))

        m = mb.addMenu('&edit')
        self.act(m, 'duplicate', self.dup_sel, QKeySequence('Ctrl+D'))
        self.act(m, 'delete', self.del_sel, QKeySequence('Del'))
        self.act(m, 'select all', self.select_all, QKeySequence('Ctrl+A'))
        m.addSeparator()
        self.act(m, 'frame all', lambda: self.canvas.frame_all(), QKeySequence('Ctrl+Shift+F'))
        self.act(m, 'zoom in', lambda: self.canvas.zoom_by(1.25))
        self.act(m, 'zoom out', lambda: self.canvas.zoom_by(0.8))
        self.act(m, 'zoom 100%', self.zoom_reset)
        m.addSeparator()
        self.act(m, 'toggle grid', self.toggle_grid)
        self.act(m, 'toggle snap', self.toggle_snap)
        m.addSeparator()
        self.act(m, 'project settings', self.project_settings)

        m = mb.addMenu('&node')
        for t in ORDER:
            self.act(m, 'add ' + t, lambda _c=False, tt=t: self.add_node(tt))
        m.addSeparator()
        self.act(m, 'bring to front', lambda: self.reorder(1))
        self.act(m, 'send to back', lambda: self.reorder(-1))

        m = mb.addMenu('&run')
        self.play_action = self.act(m, 'play', self.play, QKeySequence('F5'))
        self.stop_action = self.act(m, 'stop', self.stop, QKeySequence('F6'))
        self.stop_action.setEnabled(False)

        m = mb.addMenu('&help')
        self.act(m, 'lightscript reference', self.show_help)
        self.act(m, 'about', self.show_about)

        tb = QToolBar('main')
        tb.setObjectName('main')
        tb.setMovable(False)
        self.addToolBar(tb)
        self.play_btn = QAction('play', self)
        self.play_btn.triggered.connect(self.toggle_play)
        tb.addAction(self.play_btn)
        tb.addSeparator()
        for text, slot, tip in (('add', self.add_menu, 'add node'),
                                ('grid', self.toggle_grid, 'grid'),
                                ('snap', self.toggle_snap, 'snap to grid'),
                                ('fit', lambda: self.canvas.frame_all(), 'fit view'),
                                ('save', self.save, 'save scene')):
            a = QAction(text, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            tb.addAction(a)
        sp = QWidget()
        sp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(sp)
        self.tb_label = QLabel('')
        tb.addWidget(self.tb_label)

    def wire(self):
        self.canvas.selected.connect(self.select_node)
        self.canvas.moved.connect(self.on_moved)
        self.canvas.edited.connect(self.touch)
        self.canvas.request.connect(self.on_request)
        self.hierarchy.picked.connect(self.select_node)
        self.hierarchy.changed.connect(self.on_renamed)
        self.hierarchy.created.connect(lambda t: self.add_node(t, None, self.hierarchy.selected_node()))
        self.hierarchy.removed.connect(self.del_node)
        self.hierarchy.duplicated.connect(self.dup_node)
        self.inspector.changed.connect(self.on_prop)

    def node_types(self):
        return list(ORDER)

    # --- сцена ---

    def load_scene(self, path=None):
        path = path or (self.project.scene_path() if self.project else None)
        if path and os.path.isfile(path):
            self.scene = load_scene(path)
        else:
            self.scene = Scene('main')
            self.scene.build_starter()
            if self.project:
                path = self.project.scene_path()
                self.project.make_dirs()
                save_scene(path, self.scene)
        self.scene_path = path
        self.game.scene = self.scene
        self.game.size = self.scene.size
        self.game.input.clear()
        self.dirty = False
        self.rebuild_ui()

    def reload(self):
        if self.scene_path and os.path.isfile(self.scene_path):
            self.load_scene(self.scene_path)
            self.log('reloaded %s' % os.path.basename(self.scene_path))

    def save(self):
        if not self.scene_path:
            return self.save_as()
        save_scene(self.scene_path, self.scene)
        if self.project:
            self.project.entry = os.path.basename(self.scene_path)
            self.project.save()
        self.dirty = False
        self.set_title()
        self.statusBar().showMessage('saved %s' % self.scene_path, 2500)
        return self.scene_path

    def save_as(self):
        if not self.project:
            return None
        d = self.project.scenes if os.path.isdir(self.project.scenes) else self.project.root
        name, _ = QFileDialog.getSaveFileName(self, 'save scene', os.path.join(d, 'main.lscene'),
                                              'lightengine scene (*.lscene)')
        if not name:
            return None
        if not name.endswith('.lscene'):
            name += '.lscene'
        self.scene_path = name
        return self.save()

    def new_scene(self):
        self.scene = Scene('main')
        self.game.scene = self.scene
        self.scene_path = self.project.scene_path('main.lscene') if self.project else None
        self.dirty = True
        self.rebuild_ui()
        self.log('new scene')

    def open_scene(self):
        d = self.project.scenes if self.project else os.getcwd()
        name, _ = QFileDialog.getOpenFileName(self, 'open scene', d, 'lightengine scene (*.lscene)')
        if name:
            self.load_scene(name)
            self.log('opened %s' % os.path.basename(name))

    def node_by_id(self, nid):
        for n in self.scene.walk():
            if id(n) == nid:
                return n
        return None

    def rebuild_ui(self):
        self.hierarchy.rebuild()
        self.game.scene = self.scene
        self.game.size = self.scene.size
        self.console.reset()
        self.inspector.load(None)
        self.sel = None
        self.canvas.sel = None
        self.canvas.update()
        self.set_title()
        self.statusBar().showMessage('scene %s, %d nodes' % (self.scene.name, len(self.scene.nodes)), 2500)

    def set_title(self):
        proj = self.project.name if self.project else 'no project'
        mark = '*' if self.dirty else ''
        self.setWindowTitle('%s %s- %s [%s] - %s' % (ENGINE, mark, os.path.basename(self.scene_path or 'untitled'),
                                                     proj, AUTHOR))

    def touch(self):
        self.dirty = True
        self.set_title()

    def log(self, msg, node=None):
        if node is not None:
            self.console.report(node, msg)
        else:
            self.console.log(msg)

    # --- выбор и узлы ---

    def select_node(self, node):
        self.sel = node
        self.canvas.sel = node
        self.inspector.load(node)
        self.hierarchy.select(node)
        self.console.set_context(node)
        self.canvas.update()

    def select_all(self):
        nodes = [n for n in self.scene.nodes if n.bounds() is not None]
        if not nodes:
            return
        self.select_node(nodes[0])
        self.canvas.frame_all()

    def add_node(self, t, at=None, parent=None):
        node = make_node(t, self.unique_name(t))
        tmpl = TEMPLATES.get(t)
        if tmpl:
            node.script = tmpl % node.name if '%s' in tmpl else tmpl
        if parent is None and self.sel is not None and t == 'Node2D':
            parent = self.sel
        self.scene.add(node, parent)
        if at is None:
            if self.sel is not None:
                at = self.sel.wpos()
            else:
                at = self.canvas.to_world(self.canvas.width() / 2, self.canvas.height() / 2)
        if hasattr(node, 'pos'):
            base = node.parent.wpos() if node.parent is not None and hasattr(node.parent, 'wpos') else Vec(0, 0)
            node.pos = at - base
        self.hierarchy.rebuild(self.sel)
        self.select_node(node)
        self.touch()
        return node

    def add_menu(self):
        m = QMenu(self)
        for t in ORDER:
            m.addAction(t, lambda _c=False, tt=t: self.add_node(tt))
        m.exec(self.cursor().pos())

    def unique_name(self, t):
        base = t.lower()
        n = 1
        while self.scene.find(base) is not None:
            n += 1
            base = '%s%d' % (t.lower(), n)
        return base

    def dup_node(self, node):
        c = node.dup(self.unique_name(node.TYPE))
        if node.parent is not None:
            node.parent.add(c)
        else:
            self.scene.add(c)
        self.hierarchy.rebuild(self.sel)
        self.select_node(c)
        self.touch()
        return c

    def del_node(self, node):
        if node is None:
            return
        self.scene.remove(node)
        if self.sel is node:
            self.select_node(None)
        self.hierarchy.rebuild()
        self.inspector.load(None)
        self.touch()

    def dup_sel(self):
        if self.sel is not None:
            self.dup_node(self.sel)

    def del_sel(self):
        self.del_node(self.sel)

    def move_node(self, node, d):
        lst = node.parent.children if node.parent is not None else self.scene.nodes
        i = lst.index(node)
        j = max(0, min(len(lst) - 1, i + d))
        if i == j:
            return
        lst.insert(j, lst.pop(i))
        self.hierarchy.rebuild(self.sel)
        self.touch()

    def reorder(self, node=None, d=0):
        n = node or self.sel
        if n is None or not hasattr(n, 'z'):
            return
        n.z = max(-10000, min(10000, n.z + d * 10))
        self.touch()
        self.canvas.update()

    def on_moved(self, node):
        self.inspector.refresh()
        self.touch()

    def on_renamed(self, node):
        self.inspector.load(node)
        self.touch()

    def on_prop(self, node, key, val):
        self.touch()

    def on_request(self, what):
        if what == 'delete':
            self.del_sel()
        elif what == 'play':
            self.play()
        elif what == 'stop':
            self.stop()
        elif what == 'frame_all':
            self.canvas.frame_all()
        elif what == 'select_all':
            self.select_all()

    # --- игра ---

    def toggle_play(self):
        self.stop() if self.playing else self.play()

    def play(self):
        if self.playing or not any(n.script.strip() for n in self.scene.walk()):
            if not any(n.script.strip() for n in self.scene.walk()):
                self.log('no scripts in scene, nothing to play')
            return
        self._snapshot = [n.to_dict() for n in self.scene.nodes]
        self.playing = True
        self.game.time = 0.0
        self.game.frame = 0
        self.game.errors = []
        self.game.input.clear()
        self._last = time.perf_counter()
        self.timer.start(15)
        self.play_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.play_btn.setText('stop')
        self.canvas.setFocus()
        self.log('play')

    def stop(self):
        if not self.playing:
            return
        self.playing = False
        self.timer.stop()
        if self._snapshot is not None:
            self.scene.nodes = []
            for d in self._snapshot:
                self.scene.add(node_from_dict(d))
            self._snapshot = None
        self.game.input.clear()
        self.play_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.play_btn.setText('play')
        self.rebuild_ui()
        for name, err in self.game.errors:
            self.console.log('%s: %s' % (name, err))
        self.game.errors = []
        self.log('stop')

    def tick(self):
        now = time.perf_counter()
        dt = now - self._last
        self._last = now
        self.game.step(dt)
        self.canvas.update()
        if self.game.errors and self.game.errors[-1] != self._last_err:
            self._last_err = self.game.errors[-1]
            self.console.log('%s: %s' % (self._last_err[0], self._last_err[1]))
        self.status.setText('fps %d  nodes %d  zoom %d%%  frame %d' % (
            self.game.fps, len(list(self.scene.walk())), self.canvas.zoom * 100, self.game.frame))

    def run_window(self):
        self.save()
        from engine.gameapp import GameWindow
        self.log('opening game window')
        g = Game(Scene(self.scene.name), self.res)
        g.scene = self.scene
        g.size = self.scene.size
        w = GameWindow(g, '%s - %s' % (self.scene.name, ENGINE))
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        w.show()

    # --- проекты ---

    def new_project(self):
        d = QFileDialog.getExistingDirectory(self, 'new project folder',
                                              os.path.join(os.path.dirname(self.project.root) if self.project
                                                            else os.getcwd(), 'projects'))
        if not d:
            return
        name = os.path.basename(os.path.normpath(d))
        p = Project(d, name)
        sc = Scene(name)
        sc.size = Vec(p.w, p.h)
        sc.build_starter()
        p.make_dirs()
        p.save()
        save_scene(p.scene_path(p.entry), sc)
        self.set_project(p, p.scene_path(p.entry))
        self.log('project %s created' % name)

    def open_project(self):
        d = QFileDialog.getExistingDirectory(self, 'open project', self.project.root if self.project else '')
        if not d:
            return
        p = Project.find_near(d)
        if p is None:
            p = Project(d, os.path.basename(os.path.normpath(d)))
            p.make_dirs()
            p.save()
        self.set_project(p, p.scene_path())
        self.log('project %s opened' % p.name)

    def set_project(self, project, path=None):
        self.project = project
        self.res = Resources(project.root)
        self.game.res = self.res
        self.console.host = None
        self.console.reset()
        self.load_scene(path)
        self.assets.reload()
        self.dock_nodes.setWindowTitle('nodes - %s' % project.name)

    def project_settings(self):
        if not self.project:
            return
        w, ok1 = QInputDialog.getInt(self, 'project size', 'width', self.project.w, 320, 7680)
        h, ok2 = QInputDialog.getInt(self, 'project size', 'height', self.project.h, 240, 4320)
        if not (ok1 and ok2):
            return
        name, ok3 = QInputDialog.getText(self, 'project name', 'name', text=self.project.name)
        if not ok3:
            return
        self.project.w, self.project.h = w, h
        self.project.name = name or self.project.name
        self.project.save()
        self.scene.size = Vec(w, h)
        self.game.size = self.scene.size
        self.touch()
        self.log('project %s %dx%d' % (self.project.name, w, h))

    def build_game(self):
        if not self.project:
            return
        self.save()
        from build.build_game import build
        name, ok = QInputDialog.getText(self, 'build game', 'exe name', text=self.project.name)
        if not ok or not name.strip():
            return
        self.log('building %s, see console' % name.strip())
        ok = QMessageBox.question(self, 'build game',
                                  'pyinstaller will run, this takes a while.\nbuild %s now?' % name.strip())
        if ok != QMessageBox.StandardButton.Yes:
            return
        try:
            build(self.project, name.strip(), entry=self.scene_path)
            self.log('build done, dist in %s' % self.project.dist)
        except Exception as err:
            self.log('build failed: %s' % err)

    # --- прочее ---

    def toggle_grid(self):
        self.scene.show_grid = not self.scene.show_grid
        self.canvas.show_grid = self.scene.show_grid
        self.canvas.update()

    def toggle_snap(self):
        self.canvas.snap = not self.canvas.snap
        self.statusBar().showMessage('snap %s' % ('on' if self.canvas.snap else 'off'), 1500)

    def zoom_reset(self):
        self.canvas.zoom = 1.0
        self.canvas.update()

    def show_help(self):
        from lscript.builtins import help_text
        self.console.log(help_text())
        self.dock_console.show()
        self.dock_console.raise_()

    def show_about(self):
        QMessageBox.about(self, 'about', '%s\nprototype\n\nscript: %s\nauthor: %s' % (ENGINE, LANG, AUTHOR))

    def closeEvent(self, ev):
        if self.dirty:
            r = QMessageBox.question(self, 'quit', 'scene has unsaved changes, save?',
                                     QMessageBox.StandardButton.Save |
                                     QMessageBox.StandardButton.Discard |
                                     QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Cancel:
                ev.ignore()
                return
            if r == QMessageBox.StandardButton.Save:
                self.save()
        ev.accept()


def open_app(project=None, scene=None):
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(ENGINE)
    w = MainWindow(project, scene)
    w.show()
    return app, w
