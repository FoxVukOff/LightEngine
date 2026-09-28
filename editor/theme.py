from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

BG = '#12141b'
BG2 = '#171a23'
BG3 = '#1e222d'
LINE = '#2a3040'
FG = '#d7dce8'
DIM = '#8b93a7'
ACC = '#4fc3f7'
ACC2 = '#ffb454'
BAD = '#ff6b6b'
GOOD = '#7bdcb5'

QSS = """
QWidget {{
    background: {bg};
    color: {fg};
    font-size: 12px;
}}

QMainWindow, QDialog {{ background: {bg}; }}

QMenuBar {{ background: {bg2}; border-bottom: 1px solid {line}; padding: 2px; }}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; background: transparent; }}
QMenuBar::item:selected {{ background: {bg3}; }}
QMenu {{ background: {bg2}; border: 1px solid {line}; padding: 4px; }}
QMenu::item {{ padding: 5px 22px 5px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {acc}; color: #0d1017; }}
QMenu::separator {{ height: 1px; background: {line}; margin: 4px 8px; }}

QToolBar {{ background: {bg2}; border-bottom: 1px solid {line}; spacing: 4px; padding: 3px 6px; }}
QToolBar QToolButton {{ background: {bg3}; border: 1px solid {line}; border-radius: 5px; padding: 4px 10px; }}
QToolBar QToolButton:hover {{ border-color: {acc}; color: {acc}; }}
QToolBar QToolButton:pressed {{ background: {acc}; color: #0d1017; }}
QToolBar::separator {{ background: {line}; width: 1px; margin: 4px 4px; }}

QStatusBar {{ background: {bg2}; border-top: 1px solid {line}; color: {dim}; }}
QStatusBar::item {{ border: none; }}

QDockWidget {{ titlebar-close-icon: none; }}
QDockWidget::title {{
    background: {bg2};
    padding: 6px 8px;
    border-bottom: 1px solid {line};
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: {dim};
    font-weight: 600;
}}

QTreeWidget, QTreeView, QListWidget, QTableWidget {{
    background: {bg};
    alternate-background-color: {bg2};
    border: 1px solid {line};
    border-radius: 6px;
    selection-background-color: {acc};
    selection-color: #0d1017;
    outline: none;
    padding: 2px;
}}
QTreeWidget::item, QTreeView::item, QListWidget::item {{ padding: 3px 2px; border-radius: 4px; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: {bg3}; }}
QHeaderView::section {{
    background: {bg2};
    color: {dim};
    border: none;
    border-bottom: 1px solid {line};
    padding: 4px 6px;
}}

QPlainTextEdit, QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {bg2};
    border: 1px solid {line};
    border-radius: 5px;
    padding: 3px 6px;
    selection-background-color: {acc};
    selection-color: #0d1017;
}}
QPlainTextEdit:focus, QTextEdit:focus, QLineEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {acc}; }}
QPlainTextEdit::corner, QAbstractScrollArea::corner {{ background: {bg2}; border: none; }}

QPushButton {{
    background: {bg3};
    border: 1px solid {line};
    border-radius: 5px;
    padding: 5px 12px;
}}
QPushButton:hover {{ border-color: {acc}; color: {acc}; }}
QPushButton:pressed {{ background: {acc}; color: #0d1017; }}
QPushButton:disabled {{ color: #565d6e; background: {bg2}; }}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {line};
    border-radius: 3px;
    background: {bg2};
}}
QCheckBox::indicator:checked {{ background: {acc}; border-color: {acc}; }}

QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {bg2};
    border: 1px solid {line};
    selection-background-color: {acc};
    selection-color: #0d1017;
    outline: none;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{ background: {bg3}; border: none; width: 16px; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background: {acc}; }}

QScrollBar:vertical {{ background: {bg}; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {line}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {acc}; }}
QScrollBar:horizontal {{ background: {bg}; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {line}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {acc}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QSplitter::handle {{ background: {line}; }}
QSplitter::handle:horizontal {{ width: 3px; }}
QSplitter::handle:vertical {{ height: 3px; }}

QToolTip {{
    background: {bg3};
    color: {fg};
    border: 1px solid {acc};
    padding: 3px 6px;
    border-radius: 4px;
}}
QMessageBox {{ background: {bg2}; }}
QMessageBox QLabel {{ color: {fg}; }}
"""


def palette():
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(BG))
    p.setColor(QPalette.ColorRole.WindowText, QColor(FG))
    p.setColor(QPalette.ColorRole.Base, QColor(BG2))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(BG))
    p.setColor(QPalette.ColorRole.Text, QColor(FG))
    p.setColor(QPalette.ColorRole.Button, QColor(BG3))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(FG))
    p.setColor(QPalette.ColorRole.Highlight, QColor(ACC))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor('#0d1017'))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG3))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(FG))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(DIM))
    return p


def apply(app=None):
    app = app or QApplication.instance()
    if app is None:
        return
    app.setStyle('Fusion')
    app.setPalette(palette())
    app.setStyleSheet(QSS.format(bg=BG, bg2=BG2, bg3=BG3, line=LINE, fg=FG, dim=DIM, acc=ACC))
