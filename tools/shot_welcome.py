import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from editor.theme import apply

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
FONTS = (r'C:\Windows\Fonts\segoeui.ttf', r'C:\Windows\Fonts\segoeui_cyrillic.ttf',
         r'C:\Windows\Fonts\consola.ttf', r'C:\Windows\Fonts\arial.ttf')


def load_fonts():
    for f in FONTS:
        if os.path.isfile(f):
            QFontDatabase.addApplicationFont(f)


def main():
    app = QApplication.instance() or QApplication([])
    load_fonts()
    apply(app)
    os.makedirs(DOCS, exist_ok=True)
    from editor.welcome import Welcome
    dlg = Welcome()
    dlg.resize(660, 520)
    dlg.show()
    for i in range(4):
        app.processEvents()
    dlg.grab().save(os.path.join(DOCS, 'welcome.png'), 'PNG')
    print('wrote docs/welcome.png')


if __name__ == '__main__':
    main()
