from .errors import ScriptError

KW = {
    'let', 'const', 'if', 'elif', 'else', 'unless', 'while', 'for', 'in',
    'func', 'return', 'break', 'continue', 'repeat', 'and', 'or', 'not',
    'true', 'false', 'null', 'pass',
}

ALIASES = {'def': 'func', 'True': 'true', 'False': 'false', 'None': 'null', 'nil': 'null'}

OPS = [
    '**=', '//=', '>>=', '<<=',
    '**', '//', '==', '!=', '<=', '>=', '+=', '-=', '*=', '/=', '%=',
    '->', '|>', '??', '?.', '::', '..',
    '+', '-', '*', '/', '%', '=', '<', '>', '!', '(', ')', '[', ']', '{', '}',
    ',', '.', ';', ':', '?',
]
OPS.sort(key=len, reverse=True)

ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0', '\\': '\\', '"': '"', "'": "'", 'a': '\a', 'b': '\b'}


class Lexer:
    def __init__(self, src, file='<script>'):
        self.src = src.replace('\r\n', '\n').replace('\r', '\n').replace('\t', '    ')
        self.file = file
        self.i = 0
        self.line = 1
        self.toks = []
        self.indent = [0]
        self.line_start = True

    def err(self, msg):
        raise ScriptError('%s:%d: %s' % (self.file, self.line, msg))

    def emit(self, kind, val=None):
        self.toks.append((kind, val, self.line))
        if kind not in ('nl', 'indent', 'dedent'):
            self.content = True

    def run(self):
        src, n = self.src, len(self.src)
        self.content = False
        while self.i < n:
            if self.line_start:
                self.line_start = False
                if not self.indent_here():
                    continue
            ch = src[self.i]
            if ch == '\n':
                self.i += 1
                self.line += 1
                self.line_start = True
                if self.content:
                    self.emit('nl')
                self.content = False
                continue
            if ch == ' ':
                self.i += 1
                continue
            if ch == '#' or src.startswith('//', self.i):
                while self.i < n and src[self.i] != '\n':
                    self.i += 1
                continue
            if ch == '\\' and self.i + 1 < n and src[self.i + 1] == '\n':
                self.i += 2
                self.line += 1
                continue
            if ch in '"\'':
                self.string(ch)
                continue
            if ch.isdigit() or (ch == '.' and self.i + 1 < n and src[self.i + 1].isdigit()):
                self.number()
                continue
            if ch.isalpha() or ch in '_$':
                self.word()
                continue
            self.op()
        self.emit('nl')
        while len(self.indent) > 1:
            self.indent.pop()
            self.emit('dedent')
        self.emit('eof')
        return self.toks
    def indent_here(self):
        src, n = self.src, len(self.src)
        start = self.i
        while self.i < n and src[self.i] == ' ':
            self.i += 1
        width = self.i - start
        ch = src[self.i] if self.i < n else ''
        if ch == '' or ch == '\n' or ch == '#' or src.startswith('//', self.i):
            return False
        top = self.indent[-1]
        if width > top:
            self.indent.append(width)
            self.emit('indent')
        elif width < top:
            while len(self.indent) > 1 and self.indent[-1] > width:
                self.indent.pop()
                self.emit('dedent')
            if self.indent[-1] != width:
                self.err('bad indent %d' % width)
        return True

    def string(self, quote):
        src, n = self.src, len(self.src)
        triple = src.startswith(quote * 3, self.i)
        term = quote * 3 if triple else quote
        self.i += len(term)
        buf = []
        while True:
            if self.i >= n:
                self.err('unclosed string')
            ch = src[self.i]
            if ch == '\\':
                self.i += 1
                e = src[self.i] if self.i < n else ''
                if e == 'u':
                    buf.append(chr(int(src[self.i + 1:self.i + 5], 16)))
                    self.i += 5
                    continue
                if e == 'n' and triple:
                    self.line += 1
                buf.append(ESCAPES.get(e, '\\' + e))
                self.i += 1
                continue
            if src.startswith(term, self.i):
                self.i += len(term)
                break
            if ch == '\n':
                if not triple:
                    self.err('unclosed string')
                self.line += 1
            buf.append(ch)
            self.i += 1
        self.emit('str', ''.join(buf))

    def number(self):
        src, n = self.src, len(self.src)
        start = self.i
        if src.startswith('0x', self.i) or src.startswith('0X', self.i):
            self.i += 2
            while self.i < n and src[self.i] in '0123456789abcdefABCDEF_':
                self.i += 1
            self.emit('num', int(src[start + 2:self.i].replace('_', ''), 16))
            return
        while self.i < n and (src[self.i].isdigit() or src[self.i] == '_'):
            self.i += 1
        isf = False
        if self.i < n and src[self.i] == '.' and not src.startswith('..', self.i):
            isf = True
            self.i += 1
            while self.i < n and src[self.i].isdigit():
                self.i += 1
        if self.i < n and src[self.i] in 'eE':
            j = self.i + 1
            if j < n and src[j] in '+-':
                j += 1
            if j < n and src[j].isdigit():
                isf = True
                self.i = j
                while self.i < n and src[self.i].isdigit():
                    self.i += 1
        raw = src[start:self.i].replace('_', '')
        self.emit('num', float(raw) if isf else int(raw))

    def word(self):
        src, n = self.src, len(self.src)
        start = self.i
        while self.i < n and (src[self.i].isalnum() or src[self.i] in '_$'):
            self.i += 1
        w = ALIASES.get(src[start:self.i], src[start:self.i])
        self.emit('kw' if w in KW else 'name', w)

    def op(self):
        for o in OPS:
            if self.src.startswith(o, self.i):
                self.i += len(o)
                self.emit(o, o)
                return
        self.err('bad char %r' % self.src[self.i])


def tokenize(src, file='<script>'):
    return Lexer(src, file).run()
