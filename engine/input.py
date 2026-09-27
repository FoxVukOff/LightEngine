from PyQt6.QtCore import Qt

from .mathx import Vec

KEYS = {
    Qt.Key.Key_Space: 'space', Qt.Key.Key_Enter: 'enter', Qt.Key.Key_Return: 'enter',
    Qt.Key.Key_Escape: 'escape', Qt.Key.Key_Tab: 'tab', Qt.Key.Key_Backspace: 'backspace',
    Qt.Key.Key_Up: 'up', Qt.Key.Key_Down: 'down', Qt.Key.Key_Left: 'left', Qt.Key.Key_Right: 'right',
    Qt.Key.Key_Shift: 'shift', Qt.Key.Key_Control: 'ctrl', Qt.Key.Key_Alt: 'alt',
    Qt.Key.Key_A: 'a', Qt.Key.Key_B: 'b', Qt.Key.Key_C: 'c', Qt.Key.Key_D: 'd', Qt.Key.Key_E: 'e',
    Qt.Key.Key_F: 'f', Qt.Key.Key_G: 'g', Qt.Key.Key_H: 'h', Qt.Key.Key_I: 'i', Qt.Key.Key_J: 'j',
    Qt.Key.Key_K: 'k', Qt.Key.Key_L: 'l', Qt.Key.Key_M: 'm', Qt.Key.Key_N: 'n', Qt.Key.Key_O: 'o',
    Qt.Key.Key_P: 'p', Qt.Key.Key_Q: 'q', Qt.Key.Key_R: 'r', Qt.Key.Key_S: 's', Qt.Key.Key_T: 't',
    Qt.Key.Key_U: 'u', Qt.Key.Key_V: 'v', Qt.Key.Key_W: 'w', Qt.Key.Key_X: 'x', Qt.Key.Key_Y: 'y',
    Qt.Key.Key_Z: 'z',
}
for i in range(1, 13):
    KEYS[getattr(Qt.Key, 'Key_F%d' % i)] = 'f%d' % i

MX = {'left': -1.0, 'a': -1.0, 'right': 1.0, 'd': 1.0}
MY = {'up': -1.0, 'w': -1.0, 'down': 1.0, 's': 1.0}


def key_name(key, text=''):
    if key in KEYS:
        return KEYS[key]
    if text and text.isprintable():
        return text.lower()
    return str(key).rsplit('.', 1)[-1].lower()


class Input:
    def __init__(self):
        self.held = set()
        self.hit = set()
        self.released = set()
        self.mouse = Vec()
        self.prev_mouse = Vec()
        self.buttons = set()
        self.clicked = False
        self.right = False
        self.wheel = 0.0

    def begin(self):
        self.hit = set()
        self.released = set()
        self.clicked = False
        self.right = False
        self.wheel = 0.0

    def end(self):
        self.prev_mouse = self.mouse

    def key_down(self, name):
        if name not in self.held:
            self.hit.add(name)
        self.held.add(name)

    def key_up(self, name):
        self.held.discard(name)
        self.released.add(name)

    def clear(self):
        self.held.clear()
        self.hit.clear()
        self.released.clear()
        self.buttons.clear()

    def down(self, name):
        return name in self.held

    def pressed(self, name):
        return name in self.hit

    def up_edge(self, name):
        return name in self.released

    def axis(self):
        x = y = 0.0
        for k, v in MX.items():
            if k in self.held:
                x += v
        for k, v in MY.items():
            if k in self.held:
                y += v
        v = Vec(x, y)
        if v.len() > 1.0:
            v = v.normed()
        return v

    def mouse_move(self, x, y):
        self.mouse = Vec(x, y)

    def mouse_delta(self):
        return self.mouse - self.prev_mouse
