import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from engine import AUTHOR, ENGINE, LANG
from editor.projects import clean_name, create_project, engine_dir, list_projects, projects_dir
from editor.theme import ACC, DIM, FG


class Welcome(QDialog):
    # отдаёт выбранный проект или None

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('%s - новый проект' % ENGINE)
        self.setMinimumSize(620, 480)
        self.picked = None

        head = QLabel(ENGINE)
        head.setStyleSheet('font-size: 26px; font-weight: 700; color: %s' % ACC)
        sub = QLabel('%s для игр, движок и редактор сцен' % LANG)
        sub.setStyleSheet('color: %s; font-size: 13px' % DIM)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 'assets', 'icon.png')
        logo = QLabel()
        pm = QPixmap(icon_path)
        if not pm.isNull():
            logo.setPixmap(pm.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignTop)

        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(logo)
        headbox = QVBoxLayout()
        headbox.addWidget(head)
        headbox.addWidget(sub)
        headbox.addStretch(1)
        top.addLayout(headbox, 1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet('color: #2a3040')

        # создание нового проекта
        newbox = QLabel('новый проект')
        newbox.setStyleSheet('font-weight: 600; color: %s' % FG)
        hint = QLabel('папка создастся в %s' % projects_dir())
        hint.setStyleSheet('color: %s; font-size: 11px' % DIM)
        hint.setWordWrap(True)
        self.name = QLineEdit()
        self.name.setPlaceholderText('имя проекта, например space_drift')
        self.name.returnPressed.connect(self.make)
        self.make_btn = QPushButton('создать')
        self.make_btn.clicked.connect(self.make)
        row = QHBoxLayout()
        row.addWidget(self.name, 1)
        row.addWidget(self.make_btn)

        # открытие существующего
        openbox = QLabel('недавние проекты')
        openbox.setStyleSheet('font-weight: 600; color: %s' % FG)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.open_picked)
        self.list.itemSelectionChanged.connect(self.sel_changed)
        for p in list_projects():
            it = QListWidgetItem('%s      %dx%d      %s' % (
                p.name, p.w, p.h, os.path.relpath(p.root, engine_dir())))
            it.setData(Qt.ItemDataRole.UserRole, p.path)
            self.list.addItem(it)
        self.open_btn = QPushButton('открыть')
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_picked)
        other = QPushButton('другая папка...')
        other.clicked.connect(self.open_any)
        row2 = QHBoxLayout()
        row2.addStretch(1)
        row2.addWidget(other)
        row2.addWidget(self.open_btn)

        foot = QLabel('автор %s, проект создаётся только здесь, ничего не создаётся само' % AUTHOR)
        foot.setStyleSheet('color: %s; font-size: 11px' % DIM)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(10)
        lay.addLayout(top)
        lay.addWidget(line)
        lay.addWidget(newbox)
        lay.addWidget(hint)
        lay.addLayout(row)
        lay.addSpacing(6)
        lay.addWidget(openbox)
        lay.addWidget(self.list, 1)
        lay.addLayout(row2)
        lay.addWidget(foot)
        if self.list.count() == 0:
            self.name.setFocus()

    def sel_changed(self):
        self.open_btn.setEnabled(self.list.currentItem() is not None)

    def make(self):
        name = clean_name(self.name.text())
        if not self.name.text().strip():
            self.name.setFocus()
            return
        try:
            p = create_project(name)
        except FileExistsError:
            self.name.setText('')
            self.name.setPlaceholderText('проект %s уже есть, выбери другое имя' % name)
            return
        except OSError as e:
            self.name.setPlaceholderText('не получилось: %s' % e)
            return
        self.picked = p
        self.accept()

    def open_picked(self):
        it = self.list.currentItem()
        if it is None:
            return
        path = it.data(Qt.ItemDataRole.UserRole)
        try:
            from engine.project import Project
            self.picked = Project.open(path)
        except (OSError, ValueError) as e:
            self.list.takeItem(self.list.row(it))
            return
        self.accept()

    def open_any(self):
        path, _ = QFileDialog.getOpenFileName(self, 'выбери project.json', projects_dir(),
                                               'lightengine project (project.json)')
        if not path:
            return
        try:
            from engine.project import Project
            self.picked = Project.open(path)
        except (OSError, ValueError):
            return
        self.accept()
