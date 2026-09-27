from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

from engine.mathx import Color, Vec, to_color


class Inspector(QScrollArea):
    changed = pyqtSignal(object, str, object)
    closed = pyqtSignal()

    def __init__(self, win):
        QScrollArea.__init__(self)
        self.win = win
        self.setWidgetResizable(True)
        self.body = QWidget()
        self.form = QFormLayout(self.body)
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form.setContentsMargins(6, 6, 6, 6)
        self.setWidget(self.body)
        self.node = None
        self.widgets = {}
        self._swatch = {}
        self._spins = {}
        self._lock = False

    def clear(self):
        while self.form.count():
            item = self.form.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self.widgets = {}
        self._swatch = {}
        self._spins = {}
        self.node = None

    def load(self, node):
        self.clear()
        self.node = node
        if node is None:
            l = QLabel('nothing selected')
            l.setStyleSheet('color:#7a8296')
            self.form.addRow(l)
            return
        head = QHBoxLayout()
        t = QLabel('%s  [%s]' % (node.name, node.TYPE))
        t.setStyleSheet('font-weight:600')
        head.addWidget(t)
        for text, slot, tip in (('focus', lambda: self.win.canvas.frame_node(node), 'center view'),
                                ('dup', lambda: self.win.dup_node(node), 'duplicate'),
                                ('del', lambda: self.win.del_node(node), 'delete')):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFixedHeight(22)
            b.clicked.connect(slot)
            head.addWidget(b)
        wrap = QWidget()
        wrap.setLayout(head)
        self.form.addRow(wrap)

        for p in node.props():
            w = self.make_widget(p, getattr(node, p['name'], p['def']))
            if w is None:
                continue
            self.widgets[p['name']] = (w, p)
            self.form.addRow(p['name'], w)

    def make_widget(self, p, val):
        k = p['kind']
        if k == 'float':
            w = QDoubleSpinBox()
            w.setDecimals(3)
            w.setRange(p['lo'], p['hi'])
            w.setSingleStep(p['step'] or 1.0)
            w.setValue(float(val))
            w.valueChanged.connect(lambda v, n=p['name']: self.emit(n, v))
            return w
        if k == 'int':
            w = QDoubleSpinBox()
            w.setDecimals(0)
            w.setRange(p['lo'], p['hi'])
            w.setSingleStep(1)
            w.setValue(float(val))
            w.valueChanged.connect(lambda v, n=p['name']: self.emit(n, int(v)))
            return w
        if k == 'bool':
            w = QCheckBox()
            w.setChecked(bool(val))
            w.stateChanged.connect(lambda v, n=p['name']: self.emit(n, bool(v)))
            return w
        if k == 'str':
            w = QLineEdit(str(val))
            w.editingFinished.connect(lambda n=p['name'], b=w: self.emit(n, b.text()))
            return w
        if k == 'enum':
            w = QComboBox()
            w.addItems([str(o) for o in (p['opts'] or [])])
            w.setCurrentText(str(val))
            w.currentTextChanged.connect(lambda v, n=p['name']: self.emit(n, v))
            return w
        if k == 'color':
            return self.color_widget(p, val)
        if k == 'vec2':
            return self.vec_widget(p, val)
        if k == 'code':
            w = QPlainTextEdit(str(val))
            w.setFixedHeight(220)
            w.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            f = w.font()
            f.setStyleHint(f.StyleHint.Monospace)
            f.setFamily('Consolas')
            f.setPointSizeF(9.5)
            w.setFont(f)
            w.textChanged.connect(lambda n=p['name'], b=w: self.emit(n, b.toPlainText()))
            return w
        return None

    def color_widget(self, p, val):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        b = QPushButton()
        b.setFixedWidth(46)
        hexline = QLineEdit(to_color(val).to_hex()[:7])
        hexline.setMaxLength(9)
        b.clicked.connect(lambda: self.pick_color(p['name'], hexline))
        hexline.editingFinished.connect(lambda n=p['name'], e=hexline: self.emit(n, e.text()))
        lay.addWidget(b)
        lay.addWidget(hexline)
        self._swatch[p['name']] = b
        b.setStyleSheet('background:%s' % to_color(val).to_hex())
        return box

    def vec_widget(self, p, val):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        v = val if isinstance(val, Vec) else Vec(val)
        spins = []
        for i in (0, 1):
            s = QDoubleSpinBox()
            s.setDecimals(2)
            s.setRange(-1e7, 1e7)
            s.setSingleStep(1.0)
            s.setValue(v.x if i == 0 else v.y)
            ax = i
            s.valueChanged.connect(lambda val, n=p['name'], a=ax, box=box: self.emit_vec(n, a, val, box))
            lay.addWidget(s)
            spins.append(s)
        self._spins[p['name']] = spins
        return box

    def emit_vec(self, name, axis, val, box):
        if self._lock or self.node is None:
            return
        cur = getattr(self.node, name, Vec())
        v = Vec(val, cur.y) if axis == 0 else Vec(cur.x, val)
        self.emit(name, v, sync=False)

    def pick_color(self, name, hexline):
        cur = to_color(self.node.get_prop(name)) if self.node is not None else Color(1, 1, 1, 1)
        qc = QColor.fromRgbF(cur.r, cur.g, cur.b, cur.a)
        got = QColorDialog.getColor(qc, self, 'color')
        if got.isValid():
            c = Color(got.redF(), got.greenF(), got.blueF(), got.alphaF())
            hexline.setText(c.to_hex()[:7])
            self.emit(name, c)

    def emit(self, name, val, sync=True):
        if self._lock or self.node is None:
            return
        self.node.set_prop(name, val)
        self.changed.emit(self.node, name, val)
        if sync:
            self.sync_widget(name)
        self.win.canvas.update()

    def sync_widget(self, name):
        if self.node is None or name not in self.widgets:
            return
        w, p = self.widgets[name]
        val = getattr(self.node, name, None)
        self._lock = True
        try:
            if p['kind'] in ('float', 'int'):
                w.setValue(float(val))
            elif p['kind'] == 'bool':
                w.setChecked(bool(val))
            elif p['kind'] == 'code':
                if w.toPlainText() != (val or ''):
                    w.setPlainText(val or '')
            elif p['kind'] == 'vec2':
                for i, s in enumerate(self._spins.get(name, [])):
                    s.setValue(val.x if i == 0 else val.y)
            elif p['kind'] == 'color':
                b = self._swatch.get(name)
                if b is not None:
                    b.setStyleSheet('background:%s' % to_color(val).to_hex())
                    le = w.layout().itemAt(1).widget()
                    le.setText(to_color(val).to_hex()[:7])
        finally:
            self._lock = False

    def refresh(self):
        if self.node is None or self.node.dead:
            self.load(None)
            return
        for name in list(self.widgets):
            self.sync_widget(name)
