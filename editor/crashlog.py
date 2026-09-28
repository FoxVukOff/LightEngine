import os
import sys
import time
import traceback


def log_path(root=None):
    base = root or os.getcwd()
    try:
        d = os.path.join(base, 'logs')
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, 'error.log')
    except OSError:
        return None


def install(root=None, show=True):
    # в pyqt6 необработанное исключение в слоте убивает процесс,
    # поэтому пишем его в лог и показываем месседж, а не падаем
    path = log_path(root)
    state = {'shown': 0}
    old = sys.excepthook

    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            old(exc_type, exc, tb)
            return
        txt = ''.join(traceback.format_exception(exc_type, exc, tb))
        if path:
            try:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write('\n--- %s ---\n%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), txt))
                    if os.path.getsize(path) > 512 * 1024:
                        os.replace(path, path + '.1')
            except OSError:
                pass
        sys.stderr.write(txt)
        if not show or state['shown'] > 5:
            return
        state['shown'] += 1
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance()
            if app is None:
                return
            lines = traceback.format_exception_only(exc_type, exc)
            QMessageBox.critical(None, 'LightEngine',
                                 '%s\n\nподробности в logs/error.log' % lines[0].strip())
        except Exception:
            pass

    sys.excepthook = hook
    return hook
