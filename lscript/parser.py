from .errors import syntax_error
from .lexer import tokenize

AUG = {'**=': '**', '//=': '//', '*=': '*', '/=': '/', '%=': '%', '+=': '+', '-=': '-'}
CMP = ('==', '!=', '<', '<=', '>', '>=')
END = ('nl', 'dedent', 'eof', ';')


class Parser:
    def __init__(self, toks, file='<script>'):
        self.toks = toks
        self.p = 0
        self.file = file

    def peek(self, k=0):
        return self.toks[min(self.p + k, len(self.toks) - 1)]

    def kind(self, k=0):
        return self.peek(k)[0]

    def val(self, k=0):
        return self.peek(k)[1]

    def at(self, kind, val=None):
        t = self.peek()
        return t[0] == kind and (val is None or t[1] == val)

    def at_any(self, *kinds):
        return self.peek()[0] in kinds

    def next(self):
        t = self.toks[self.p]
        if t[0] != 'eof':
            self.p += 1
        return t

    def accept(self, kind, val=None):
        if self.at(kind, val):
            return self.next()
        return None

    def expect(self, kind, val=None):
        if not self.at(kind, val):
            self.err('expected %s but got %r' % (val or kind, self.peek()[1]))
        return self.next()

    def err(self, msg):
        raise syntax_error(self.file, self.peek()[2], msg)

    # --- statements ---

    def module(self):
        stmts = []
        while not self.at('eof'):
            if self.accept('nl') or self.accept(';'):
                continue
            if self.stmt_into(stmts) and not self.at_any(*END):
                self.err('unexpected %r' % self.peek()[1])
        return stmts

    def stmt_into(self, out):
        line = self.peek()[2]
        st = self.stmt()
        out.append(('ln', line, st))
        return st[0] not in ('if', 'while', 'for', 'repeat', 'func', 'unless')

    def block(self):
        self.expect(':')
        if self.accept('nl'):
            self.expect('indent')
            stmts = []
            while not self.at_any('dedent', 'eof'):
                if self.accept('nl') or self.accept(';'):
                    continue
                self.stmt_into(stmts)
            self.accept('dedent')
            return stmts
        stmts = []
        while not self.at_any(*END):
            self.stmt_into(stmts)
        return stmts

    def stmt(self):
        if self.at('kw'):
            v = self.val()
            if v in ('let', 'const'):
                return self.decl(v == 'const')
            if v == 'if':
                return self.if_stmt()
            if v == 'unless':
                self.next()
                cond = ('un', 'not', self.expr())
                return ('if', [(cond, self.block())], None)
            if v == 'while':
                self.next()
                return ('while', self.expr(), self.block())
            if v == 'for':
                self.next()
                names = [self.expect('name')[1]]
                while self.accept(','):
                    names.append(self.expect('name')[1])
                self.expect('kw', 'in')
                return ('for', names, self.expr(), self.block())
            if v == 'repeat':
                self.next()
                cnt = None if self.at_any('nl', ':') else self.expr()
                return ('repeat', cnt, self.block())
            if v == 'func':
                return self.func_stmt()
            if v == 'return':
                self.next()
                val = None if self.at_any(*END) else self.expr()
                return ('ret', val)
            if v == 'break':
                self.next()
                return ('break',)
            if v == 'continue':
                self.next()
                return ('cont',)
            if v == 'pass':
                self.next()
                return ('pass',)
        return self.simple_stmt()

    def decl(self, is_const):
        self.next()
        name = self.expect('name')[1]
        val = self.expr() if self.accept('=') else None
        return ('let', name, val, is_const)

    def if_stmt(self):
        self.next()
        branches = []
        branches.append((self.expr(), self.block()))
        els = None
        while self.at('kw', 'elif'):
            self.next()
            branches.append((self.expr(), self.block()))
        if self.at('kw', 'else'):
            self.next()
            els = self.block()
        return ('if', branches, els)

    def func_stmt(self):
        self.next()
        name = self.expect('name')[1]
        self.expect('(')
        params = []
        while not self.at(')'):
            params.append((self.expect('name')[1], self.expr() if self.accept('=') else None))
            if not self.accept(','):
                break
        self.expect(')')
        return ('func', name, params, self.block())

    def simple_stmt(self):
        if self.at('name') and self.peek(1)[0] == ':':
            fn = self.next()[1]
            return ('func', fn, [], self.block())
        e = self.expr()
        if self.at(':') and e[0] == 'call' and e[1][0] == 'name':
            return ('func', e[1][1], self.def_params(e[2], e[3]), self.block())
        for op, base in AUG.items():
            if self.at(op):
                self.next()
                return ('aug', e, base, self.expr())
        if self.at_any('='):
            targets = []
            while self.accept('='):
                targets.append(e)
                e = self.expr()
            for t in reversed(targets):
                e = ('set', t, e)
            return e
        return ('expr', e)

    def def_params(self, args, kwargs):
        params = []
        for a in args:
            if a[0] != 'name':
                self.err('func args must be names')
            params.append((a[1], None))
        for k, v in kwargs:
            params = [(n, v if n == k else d) for n, d in params]
        return params

    # --- expressions ---

    def expr(self):
        e = self.coalesce()
        if self.accept('?'):
            a = self.expr()
            self.expect(':')
            return ('cond', e, a, self.expr())
        if self.at('kw', 'if'):
            self.next()
            c = self.expr()
            self.expect('kw', 'else')
            return ('cond', c, e, self.expr())
        return e

    def coalesce(self):
        e = self.logic_or()
        while self.accept('??'):
            e = ('coalesce', e, self.logic_or())
        return e

    def logic_or(self):
        e = self.logic_and()
        while self.at('kw', 'or'):
            self.next()
            e = ('logic', 'or', e, self.logic_and())
        return e

    def logic_and(self):
        e = self.logic_not()
        while self.at('kw', 'and'):
            self.next()
            e = ('logic', 'and', e, self.logic_not())
        return e

    def logic_not(self):
        if self.at('kw', 'not') or self.at('!'):
            self.next()
            return ('un', 'not', self.logic_not())
        return self.cmp_expr()

    def cmp_expr(self):
        e = self.arith()
        while self.kind() in CMP or self.at('kw', 'in'):
            op = self.next()[1]
            if op == 'in':
                e = ('cmp', 'in', e, self.arith())
            else:
                e = ('cmp', op, e, self.arith())
        return e

    def arith(self):
        e = self.term()
        while self.at_any('+', '-'):
            op = self.next()[1]
            e = ('bin', op, e, self.term())
        return e

    def term(self):
        e = self.unary()
        while self.at_any('*', '/', '%', '//'):
            op = self.next()[1]
            e = ('bin', op, e, self.unary())
        return e

    def unary(self):
        if self.at_any('-', '+'):
            op = self.next()[1]
            return ('un', op, self.unary())
        if self.at('!'):
            self.next()
            return ('un', 'not', self.unary())
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            if self.at('('):
                args, kwargs = self.args()
                e = ('call', e, args, kwargs)
            elif self.at('['):
                self.next()
                idx = self.expr()
                self.expect(']')
                e = ('index', e, idx)
            elif self.at('.'):
                self.next()
                e = ('attr', e, self.expect('name')[1])
            elif self.at('?.'):
                self.next()
                e = ('attr_opt', e, self.expect('name')[1])
            elif self.at('|>'):
                self.next()
                callee = self.pipe_target()
                args, kwargs = ([], []) if not self.at('(') else self.args()
                e = ('call', callee, [e] + args, kwargs)
            elif self.at('..'):
                self.next()
                hi = self.postfix()
                step = self.postfix() if self.at('..') else None
                if self.at('..'):
                    self.next()
                e = ('range', e, hi, step)
            else:
                return e

    def pipe_target(self):
        e = self.primary()
        while True:
            if self.at('.'):
                self.next()
                e = ('attr', e, self.expect('name')[1])
            elif self.at('?.'):
                self.next()
                e = ('attr_opt', e, self.expect('name')[1])
            elif self.at('['):
                self.next()
                idx = self.expr()
                self.expect(']')
                e = ('index', e, idx)
            else:
                return e

    def args(self):
        self.expect('(')
        args, kwargs = [], []
        while not self.at(')'):
            if self.at('name') and self.peek(1)[0] == '=':
                key = self.next()[1]
                self.next()
                kwargs.append((key, self.expr()))
            else:
                args.append(self.expr())
            if not self.accept(','):
                break
        self.expect(')')
        return args, kwargs

    def primary(self):
        k, v = self.kind(), self.val()
        if k == 'num' or k == 'str':
            self.next()
            return ('lit', v)
        if k == 'name':
            self.next()
            return ('name', v)
        if k == 'kw':
            if v in ('true', 'false'):
                self.next()
                return ('lit', v == 'true')
            if v == 'null':
                self.next()
                return ('lit', None)
        if k == '(':
            self.next()
            e = self.expr()
            self.expect(')')
            return e
        if k == '[':
            self.next()
            items = []
            while not self.at(']'):
                items.append(self.expr())
                if not self.accept(','):
                    break
            self.expect(']')
            return ('list', items)
        if k == '{':
            self.next()
            pairs = []
            while not self.at('}'):
                key = self.expr()
                self.expect(':')
                pairs.append((key, self.expr()))
                if not self.accept(','):
                    break
            self.expect('}')
            return ('dict', pairs)
        self.err('unexpected %r' % (v,))


def parse(src, file='<script>'):
    return Parser(tokenize(src, file), file).module()
