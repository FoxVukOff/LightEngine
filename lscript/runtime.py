import math

from .errors import ScriptError
from engine.mathx import Vec, Color


class Env:
    __slots__ = ('vars', 'parent')

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name, default=None):
        e = self
        while e is not None:
            v = e.vars.get(name, _MISS)
            if v is not _MISS:
                return v
            e = e.parent
        return default

    def has(self, name):
        e = self
        while e is not None:
            if name in e.vars:
                return True
            e = e.parent
        return False

    def set(self, name, val):
        e = self
        while e is not None:
            if name in e.vars:
                e.vars[name] = val
                return val
            e = e.parent
        self.vars[name] = val
        return val

    def define(self, name, val):
        self.vars[name] = val
        return val


_MISS = object()


class Ret(Exception):
    def __init__(self, val):
        self.val = val


class Brk(Exception):
    pass


class Cont(Exception):
    pass


class Range:
    __slots__ = ('start', 'stop', 'step')

    def __init__(self, start, stop, step=1):
        if step == 0:
            raise ScriptError('range step is zero')
        self.start, self.stop, self.step = int(start), int(stop), int(step)

    def count(self):
        if self.step > 0:
            n = (self.stop - self.start + self.step - 1) // self.step
        else:
            n = (self.start - self.stop - self.step - 1) // (-self.step)
        return max(0, n)

    def __len__(self):
        return self.count()

    def __iter__(self):
        i = 0
        n = self.count()
        while i < n:
            yield self.start + i * self.step
            i += 1

    def __getitem__(self, i):
        if i < 0:
            i += self.count()
        if i < 0 or i >= self.count():
            raise ScriptError('index out of range')
        return self.start + i * self.step

    def __contains__(self, v):
        return v in list(self)

    def __repr__(self):
        if self.step == 1:
            return 'range(%d, %d)' % (self.start, self.stop)
        return 'range(%d, %d, %d)' % (self.start, self.stop, self.step)


class Func:
    def __init__(self, name, params, body, env, interp):
        self.name = name
        self.params = params
        self.body = body
        self.env = env
        self.interp = interp

    def __call__(self, *args, **kw):
        return self.interp.invoke(self, args, kw)

    def __repr__(self):
        return 'func %s(%s)' % (self.name, ', '.join(p[0] for p in self.params))


def truthy(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (str, list, tuple, dict, set)):
        return len(v) > 0
    if isinstance(v, (Vec, Color, Range)):
        return bool(v)
    return True


def iterate(v):
    if isinstance(v, list):
        return list(v)
    if isinstance(v, str):
        return list(v)
    if isinstance(v, dict):
        return list(v.keys())
    if isinstance(v, Range):
        return list(v)
    if isinstance(v, Vec):
        return [v.x, v.y]
    if isinstance(v, Color):
        return list(v.to_list())
    if v is None:
        return []
    raise ScriptError('cannot iterate %s' % type_name(v))


def type_name(v):
    tag = getattr(v, 'ls_type', None)
    if tag:
        return tag
    return {
        type(None): 'null', bool: 'bool', int: 'int', float: 'float', str: 'str',
        list: 'list', dict: 'dict', Vec: 'vec2', Color: 'color', Func: 'func',
    }.get(type(v), type(v).__name__)


def dump(v):
    if isinstance(v, dict):
        return '{' + ', '.join('%r: %r' % (k, dump(x)) for k, x in v.items()) + '}'
    if isinstance(v, list):
        return '[' + ', '.join(dump(x) for x in v) + ']'
    if isinstance(v, Color):
        return v.to_hex()
    return repr(v)


def bin_op(op, a, b):
    if op == '+':
        if isinstance(a, Vec) and isinstance(b, Vec):
            return a + b
        if isinstance(a, Color) and isinstance(b, Color):
            return a + b if False else a.mix(b, 1.0)
        if isinstance(a, list) and isinstance(b, list):
            return a + b
        if isinstance(a, str):
            return a + to_str(b)
        if isinstance(a, dict) and isinstance(b, dict):
            d = dict(a)
            d.update(b)
            return d
    elif op == '-':
        if isinstance(a, Vec):
            return a - b
    elif op == '*':
        if isinstance(a, Vec):
            return a * b
        if isinstance(a, Color):
            return a * b
        if isinstance(a, str) and isinstance(b, int):
            return a * max(0, b)
    elif op == '/':
        if isinstance(a, Vec):
            return a / b
    try:
        if op == '+':
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '/':
            return a / b
        if op == '//':
            return a // b
        if op == '%':
            return a % b
        if op == '**':
            return a ** b
    except TypeError as e:
        raise ScriptError('bad operands for %s: %s' % (op, e))
    raise ScriptError('bad op %r for %s and %s' % (op, type_name(a), type_name(b)))


def to_str(v):
    if isinstance(v, str):
        return v
    if isinstance(v, Color):
        return v.to_hex()
    if isinstance(v, Vec):
        return 'vec2(%.2f, %.2f)' % (v.x, v.y)
    if isinstance(v, Func):
        return repr(v)
    return dump(v)


def get_item(obj, idx):
    if isinstance(obj, dict):
        if isinstance(idx, str):
            if idx in obj:
                return obj[idx]
            raise ScriptError('no key %r' % idx)
        if idx in obj:
            return obj[idx]
        return obj.get(idx)
    if isinstance(obj, (list, str, Range)):
        return obj[int(idx)]
    if isinstance(obj, Vec):
        return (obj.x, obj.y)[int(idx)]
    raise ScriptError('cannot index %s' % type_name(obj))


def set_item(obj, idx, val):
    if isinstance(obj, dict):
        obj[idx] = val
        return val
    if isinstance(obj, list):
        i = int(idx)
        if i < 0:
            i += len(obj)
        if i < 0 or i >= len(obj):
            raise ScriptError('index out of range')
        obj[i] = val
        return val
    raise ScriptError('cannot assign into %s' % type_name(obj))


def get_attr(obj, name):
    if isinstance(obj, dict):
        if name in obj:
            return obj[name]
    if isinstance(obj, (list, str)) and name == 'len':
        return len(obj)
    if isinstance(obj, (list, str, tuple, Vec, Color, dict, Range)) and name == 'count':
        return len(obj)
    if hasattr(obj, name):
        return getattr(obj, name)
    raise ScriptError('no field %r on %s' % (name, type_name(obj)))


def set_attr(obj, name, val):
    if isinstance(obj, dict):
        obj[name] = val
        return val
    if hasattr(obj, name):
        setattr(obj, name, val)
        return val
    raise ScriptError('no field %r on %s' % (name, type_name(obj)))


class Interp:
    def __init__(self, file='<script>', limit=3_000_000):
        self.file = file
        self.line = 0
        self.limit = limit
        self.steps = 0

    def err(self, msg):
        raise ScriptError('%s:%d: %s' % (self.file, self.line, msg))

    def step(self):
        self.steps += 1
        if self.steps > self.limit:
            self.steps = 0
            raise ScriptError('script run limit hit, probably an endless loop')

    def run(self, stmts, env):
        try:
            self.exec_block(stmts, env)
        except Ret:
            pass

    def invoke(self, fn, args, kw=None):
        env = Env(fn.env)
        kw = kw or {}
        for i, (pname, default) in enumerate(fn.params):
            if pname in kw:
                env.define(pname, kw[pname])
            elif i < len(args):
                env.define(pname, args[i])
            elif default is not None:
                env.define(pname, self.eval(default, fn.env))
            else:
                self.err('func %s needs arg %s' % (fn.name, pname))
        if len(args) > len(fn.params):
            self.err('too many args in %s' % fn.name)
        try:
            self.exec_block(fn.body, env)
        except Ret as r:
            return r.val
        return None

    def call(self, fn, args, kw=None):
        self.step()
        kw = dict(kw or ())
        if isinstance(fn, Func):
            return self.invoke(fn, args, kw)
        if callable(fn):
            try:
                return fn(*args, **kw)
            except TypeError as e:
                raise ScriptError('bad call: %s' % e)
        if isinstance(fn, (Vec, Color)) and not args:
            return fn.copy()
        self.err('value is not callable: %s' % type_name(fn))

    # --- statements ---

    def exec_block(self, stmts, env):
        for s in stmts:
            if s[0] == 'ln':
                self.line = s[1]
                self.step()
                s = s[2]
            k = s[0]
            if k == 'expr':
                self.eval(s[1], env)
            elif k == 'pass':
                pass
            elif k == 'let':
                self.do_let(s, env)
            elif k == 'set':
                self.do_set(s, env)
            elif k == 'aug':
                self.do_aug(s, env)
            elif k == 'if':
                self.do_if(s, env)
            elif k == 'while':
                self.do_while(s, env)
            elif k == 'for':
                self.do_for(s, env)
            elif k == 'repeat':
                self.do_repeat(s, env)
            elif k == 'func':
                env.define(s[1], Func(s[1], s[2], s[3], env, self))
            elif k == 'ret':
                val = None if s[1] is None else self.eval(s[1], env)
                raise Ret(val)
            elif k == 'break':
                raise Brk()
            elif k == 'cont':
                raise Cont()

    def do_let(self, s, env):
        name, val = s[1], s[2]
        if s[3] and val is None:
            self.err('const %s needs a value' % name)
        env.set(name, None if val is None else self.eval(val, env))

    def do_set(self, s, env):
        t = s[1]
        v = self.eval(s[2], env)
        k = t[0]
        if k == 'name':
            env.set(t[1], v)
        elif k == 'index':
            set_item(self.eval(t[1], env), self.eval(t[2], env), v)
        elif k == 'attr':
            set_attr(self.eval(t[1], env), t[2], v)
        else:
            self.err('bad assign target')

    def do_aug(self, s, env):
        t, op, rv = s[1], s[2], s[3]
        k = t[0]
        if k == 'name':
            self.do_set(('set', t, ('bin', op, t, rv)), env)
        elif k == 'index':
            obj, idx = t[1], t[2]
            cur = get_item(self.eval(obj, env), self.eval(idx, env))
            set_item(self.eval(obj, env), self.eval(idx, env), bin_op(op, cur, self.eval(rv, env)))
        elif k == 'attr':
            obj = self.eval(t[1], env)
            set_attr(obj, t[2], bin_op(op, get_attr(obj, t[2]), self.eval(rv, env)))
        else:
            self.err('bad assign target')

    def do_if(self, s, env):
        for cond, body in s[1]:
            if truthy(self.eval(cond, env)):
                self.exec_block(body, env)
                return
        if s[2] is not None:
            self.exec_block(s[2], env)

    def do_while(self, s, env):
        while truthy(self.eval(s[1], env)):
            self.step()
            try:
                self.exec_block(s[2], env)
            except Brk:
                return
            except Cont:
                pass

    def do_for(self, s, env):
        names = s[1] if isinstance(s[1], list) else [s[1]]
        src = self.eval(s[2], env)
        if len(names) > 1 and isinstance(src, dict):
            items = [[k, v] for k, v in src.items()]
        else:
            items = iterate(src)
        for item in items:
            self.step()
            if len(names) == 1:
                env.set(names[0], item)
            else:
                pair = [item.get('k'), item.get('v')] if isinstance(item, dict) else list(item)
                if len(pair) < len(names):
                    self.err('cannot unpack %d values in for' % len(pair))
                for nm, val in zip(names, pair):
                    env.set(nm, val)
            try:
                self.exec_block(s[3], env)
            except Brk:
                return
            except Cont:
                pass

    def do_repeat(self, s, env):
        if s[1] is None:
            n = None
        else:
            n = int(self.eval(s[1], env))
            if n < 0:
                n = None
        i = 0
        while n is None or i < n:
            self.step()
            i += 1
            try:
                self.exec_block(s[2], env)
            except Brk:
                return
            except Cont:
                pass

    # --- expressions ---

    def eval(self, e, env):
        k = e[0]
        if k == 'lit':
            return e[1]
        if k == 'name':
            v = env.get(e[1], _MISS)
            if v is _MISS:
                self.err('unknown name %r' % e[1])
            return v
        if k == 'bin':
            return bin_op(e[1], self.eval(e[2], env), self.eval(e[3], env))
        if k == 'un':
            v = self.eval(e[2], env)
            if e[1] == 'not':
                return not truthy(v)
            if e[1] == '-':
                return -v
            return +v
        if k == 'cmp':
            return self.cmp(e[1], self.eval(e[2], env), self.eval(e[3], env))
        if k == 'logic':
            l = self.eval(e[2], env)
            if e[1] == 'and':
                return self.eval(e[3], env) if truthy(l) else l
            return l if truthy(l) else self.eval(e[3], env)
        if k == 'coalesce':
            l = self.eval(e[1], env)
            return l if truthy(l) else self.eval(e[2], env)
        if k == 'cond':
            return self.eval(e[2], env) if truthy(self.eval(e[1], env)) else self.eval(e[3], env)
        if k == 'list':
            return [self.eval(x, env) for x in e[1]]
        if k == 'dict':
            return {self.eval(kk, env): self.eval(vv, env) for kk, vv in e[1]}
        if k == 'call':
            fn = self.eval(e[1], env)
            args = [self.eval(a, env) for a in e[2]]
            kw = {n: self.eval(v, env) for n, v in e[3]}
            return self.call(fn, args, kw)
        if k == 'index':
            return get_item(self.eval(e[1], env), self.eval(e[2], env))
        if k == 'attr':
            return get_attr(self.eval(e[1], env), e[2])
        if k == 'attr_opt':
            o = self.eval(e[1], env)
            if o is None:
                return None
            try:
                return get_attr(o, e[2])
            except ScriptError:
                return None
        if k == 'range':
            a = self.eval(e[1], env)
            b = self.eval(e[2], env)
            c = 1 if e[3] is None else self.eval(e[3], env)
            return Range(a, b, c)
        self.err('bad node %r' % (k,))

    def cmp(self, op, a, b):
        if op == '==':
            return a == b
        if op == '!=':
            return a != b
        if op == 'in':
            try:
                return b in iterate(a) or a in iterate(b)
            except ScriptError:
                return False
        if isinstance(a, (Vec, Color)) and isinstance(b, (Vec, Color)):
            raise ScriptError('cannot compare %s with %s' % (type_name(a), type_name(b)))
        if op == '<':
            return a < b
        if op == '<=':
            return a <= b
        if op == '>':
            return a > b
        return a >= b
