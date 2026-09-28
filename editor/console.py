from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                             QVBoxLayout, QWidget)

from lscript.builtins import help_text
from lscript.errors import ScriptError
from lscript.parser import parse
from lscript.runtime import Env, Interp, to_str

from engine.nodescript import Ctx, NodeApi, ScriptHost

MAX_LINES = 800


class Input(QLineEdit):
    def __init__(self, con):
        QLineEdit.__init__(self)
        self.con = con

    def keyPressEvent(self, ev):
        con = self.con
        if ev.key() == Qt.Key.Key_Up:
            con.recall(-1)
            return
        if ev.key() == Qt.Key.Key_Down:
            con.recall(1)
            return
        if ev.key() == Qt.Key.Key_L and ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            con.clear()
            return
        QLineEdit.keyPressEvent(self, ev)


class Console(QWidget):
    def __init__(self, win):
        QWidget.__init__(self)
        self.win = win
        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        self.out.setMaximumBlockCount(MAX_LINES)
        f = self.out.font()
        f.setFamily('Consolas')
        f.setPointSizeF(9.5)
        self.out.setFont(f)

        self.inp = Input(self)
        self.inp.setPlaceholderText('lightscript: self is the selected node, help() for the list')
        self.inp.returnPressed.connect(self.run)
        self.inp.setMaximumHeight(24)

        self.tag = QLabel('-')
        self.tag.setMaximumWidth(110)
        self.tag.setStyleSheet('color:#8a93a8')

        b = QPushButton('run')
        b.setFixedHeight(24)
        b.clicked.connect(self.run)
        clr = QPushButton('clr')
        clr.setFixedHeight(24)
        clr.clicked.connect(self.clear)

        bar = QHBoxLayout()
        bar.setContentsMargins(4, 0, 4, 0)
        bar.addWidget(self.tag)
        bar.addWidget(self.inp, 1)
        bar.addWidget(b)
        bar.addWidget(clr)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(self.out, 1)
        lay.addLayout(bar)

        self.hist = []
        self.hi = 0
        self.host = None
        self.env = None
        first = self.host is None
        self.reset()
        if first:
            self.log('lightscript console, help() for the list')

    def reset(self):
        sc = self.win.scene
        res = self.win.res
        if self.host is not None:
            self.host.scene = sc
        else:
            self.host = ScriptHost(sc, res)
        self.ctx_ = Ctx(self.host)
        env = Env()
        env.vars.update(self.ctx_.globals)
        env.define('help', lambda: help_text())
        self.env = env
        self.interp = Interp('console')

    def node(self):
        n = self.win.sel
        if n is None and self.win.scene.nodes:
            n = self.win.scene.nodes[0]
        return n

    def set_context(self, node):
        self.tag.setText(node.name if node is not None else '-')

    def log(self, text):
        self.out.appendPlainText(str(text))

    def report(self, node, msg):
        self.log('[%s] %s' % (node, msg))

    def clear(self):
        self.out.clear()

    def recall(self, d):
        self.hi = max(0, min(len(self.hist), self.hi + d))
        self.inp.setText(self.hist[self.hi] if self.hi < len(self.hist) else '')

    def run(self):
        src = self.inp.text().strip()
        if not src:
            return
        self.hist.append(src)
        self.hi = len(self.hist)
        self.inp.clear()
        self.log('> ' + src)
        if self.win.scene is not self.host.scene:
            self.reset()
        n = self.node()
        if n is not None:
            self.env.define('self', NodeApi(n, self.ctx_))
        self.host.scene = self.win.scene
        self.host.screen = self.win.scene.size
        try:
            stmts = parse(src, 'console')
        except ScriptError as e:
            self.log('err: %s' % e)
            return
        except Exception as e:
            self.log('err: %s: %s' % (type(e).__name__, e))
            return
        single = len(stmts) == 1 and stmts[0][0] == 'ln' and stmts[0][2][0] == 'expr'
        try:
            if single:
                self.log('= ' + to_str(self.interp.eval(stmts[0][2][1], self.env)))
            else:
                self.interp.run(stmts, self.env)
        except ScriptError as e:
            self.log('err: %s' % e)
        except RecursionError:
            self.log('err: stack overflow')
        except Exception as e:
            self.log('err: %s: %s' % (type(e).__name__, e))
        if n is not None:
            self.win.inspector.load(n)
        self.win.canvas.update()
