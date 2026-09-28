import os
import shutil

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QAbstractItemView, QFileDialog, QHBoxLayout, QLabel, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)


class Assets(QWidget):
    """список файлов проекта, двойной клик ставит текстуру в выбранный узел"""

    used = pyqtSignal(str)

    def __init__(self, win):
        QWidget.__init__(self)
        self.win = win
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.itemDoubleClicked.connect(self.pick)
        self.tree.itemClicked.connect(self.show_preview)
        self.preview = QLabel('-')
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(70)
        self.preview.setStyleSheet('background:#101218;border:1px solid #2a2f3d;color:#9aa3b5')

        imp = QPushButton('import png')
        imp.setFixedHeight(24)
        imp.clicked.connect(self.import_file)
        ref = QPushButton('refresh')
        ref.setFixedHeight(24)
        ref.clicked.connect(self.reload)

        bar = QHBoxLayout()
        bar.setContentsMargins(2, 0, 2, 0)
        bar.addWidget(imp)
        bar.addWidget(ref)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(self.preview)
        lay.addWidget(self.tree, 1)
        lay.addLayout(bar)
        self.reload()

    def reload(self):
        self.tree.clear()
        files = self.win.res.list_assets()
        root = QTreeWidgetItem(self.tree)
        root.setText(0, '%s (%d)' % (self.win.project.name if self.win.project else 'assets',
                                     len(files['img']) + len(files['snd'])))
        for kind, items in (('img', files['img']), ('snd', files['snd'])):
            if not items:
                continue
            group = QTreeWidgetItem(root)
            group.setText(0, 'текстуры' if kind == 'img' else 'звуки')
            for f in items:
                it = QTreeWidgetItem(group)
                it.setText(0, f)
                it.setData(0, Qt.ItemDataRole.UserRole, f)
                it.setData(0, Qt.ItemDataRole.UserRole + 1, kind)
        self.tree.expandAll()

    def import_file(self):
        if not self.win.project:
            return
        names, _ = QFileDialog.getOpenFileNames(self, 'import assets', self.win.project.assets,
                                                'assets (*.png *.jpg *.jpeg *.bmp *.gif *.wav *.ogg *.mp3)')
        if not names:
            return
        for n in names:
            dst = os.path.join(self.win.project.assets, os.path.basename(n))
            if os.path.abspath(n) != os.path.abspath(dst):
                shutil.copyfile(n, dst)
        self.win.log('imported %d files' % len(names))
        self.reload()

    def show_preview(self, item, col):
        f = item.data(0, Qt.ItemDataRole.UserRole)
        kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not f or kind != 'img':
            self.preview.setText('-')
            return
        pm = self.win.res.image(f)
        if pm is None:
            self.preview.setText('нет файла')
            return
        self.preview.setPixmap(pm.scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation))

    def pick(self, item, col):
        f = item.data(0, Qt.ItemDataRole.UserRole)
        kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not f:
            return
        n = self.win.sel
        if n is None:
            self.win.console.log('выбери узел, потом кликни по ассету')
            return
        if kind == 'img' and n.pdef('texture') is not None:
            n.set_prop('texture', f)
            self.win.inspector.load(n)
            self.win.touch()
            self.win.canvas.update()
            self.used.emit(f)
            self.win.console.log('texture set on %s' % n.name)
        else:
            self.win.console.log('%s: это не текстура для %s' % (f, n.TYPE))
