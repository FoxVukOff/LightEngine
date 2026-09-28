from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QAbstractItemView, QHBoxLayout, QMenu, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)


class Hierarchy(QWidget):
    picked = pyqtSignal(object)
    changed = pyqtSignal(object)
    created = pyqtSignal(str)
    removed = pyqtSignal(object)
    duplicated = pyqtSignal(object)

    def __init__(self, win):
        QWidget.__init__(self)
        self.win = win
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.menu)
        self.tree.itemClicked.connect(self.click)
        self.tree.itemDoubleClicked.connect(self.rename)
        self.tree.itemChanged.connect(self.renamed)

        bar = QHBoxLayout()
        bar.setContentsMargins(2, 2, 2, 2)
        for text, slot, tip in (('+', self.add_menu, 'add node'),
                                ('dup', self.dup, 'duplicate'),
                                ('del', self.delete, 'delete node'),
                                ('^', lambda: self.move(-1), 'move up'),
                                ('v', lambda: self.move(1), 'move down')):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFixedHeight(24)
            b.clicked.connect(slot)
            bar.addWidget(b)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(self.tree)
        lay.addLayout(bar)
        self._items = {}

    def rebuild(self, keep=None):
        self.tree.blockSignals(True)
        self.tree.clear()
        self._items = {}
        for n in self.win.scene.nodes:
            self.add_item(n, self.tree.invisibleRootItem())
        self.tree.expandAll()
        self.tree.blockSignals(False)
        if keep is not None:
            self.select(keep)

    def add_item(self, node, parent):
        it = QTreeWidgetItem(parent)
        it.setText(0, node.name)
        it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
        it.setToolTip(0, node.TYPE)
        f = it.font(0)
        f.setPointSizeF(9.0)
        it.setFont(0, f)
        it.setData(0, Qt.ItemDataRole.UserRole, id(node))
        self._items[id(node)] = it
        for c in node.children:
            self.add_item(c, it)
        return it

    def item_for(self, node):
        it = self._items.get(id(node))
        if it is not None and it.parent() is not None:
            return it
        if node in self.win.scene.nodes:
            return self.add_item(node, self.tree.invisibleRootItem())
        return None

    def select(self, node):
        self.tree.blockSignals(True)
        self.tree.clearSelection()
        it = self.item_for(node) if node is not None else None
        if it is not None:
            it.setSelected(True)
            self.tree.setCurrentItem(it)
            self.tree.scrollToItem(it)
        self.tree.blockSignals(False)

    def click(self, item, col):
        node = self.win.node_by_id(item.data(0, Qt.ItemDataRole.UserRole))
        if node is not None:
            self.picked.emit(node)

    def renamed(self, item, col):
        node = self.win.node_by_id(item.data(0, Qt.ItemDataRole.UserRole))
        if node is None:
            return
        name = item.text(0).strip() or node.name
        if name == node.name:
            return
        node.name = name
        if item.text(0) != name:
            self.tree.blockSignals(True)
            item.setText(0, name)
            self.tree.blockSignals(False)
        self.changed.emit(node)

    def rename(self, item):
        self.tree.editItem(item, 0)

    def add_menu(self):
        m = QMenu(self)
        for t in self.win.node_types():
            m.addAction(t, lambda _c=False, tt=t: self.created.emit(tt))
        m.exec(self.cursor().pos())

    def selected_node(self):
        it = self.tree.currentItem()
        if it is None:
            return None
        return self.win.node_by_id(it.data(0, Qt.ItemDataRole.UserRole))

    def dup(self):
        n = self.selected_node()
        if n is not None:
            self.duplicated.emit(n)

    def delete(self):
        n = self.selected_node()
        if n is not None:
            self.removed.emit(n)

    def move(self, d):
        n = self.selected_node()
        if n is None:
            return
        self.win.move_node(n, d)

    def menu(self, pos):
        n = self.selected_node()
        m = QMenu(self)
        for t in self.win.node_types():
            m.addAction(t, lambda _c=False, tt=t: self.win.add_node(tt, None, n))
        if n is not None:
            m.addSeparator()
            m.addAction('rename', lambda: self.rename(self.item_for(n)))
            m.addAction('duplicate', lambda: self.duplicated.emit(n))
            m.addAction('delete', lambda: self.removed.emit(n))
            m.addAction('select in canvas', lambda: self.win.select_node(n))
        m.exec(self.tree.viewport().mapToGlobal(pos))
