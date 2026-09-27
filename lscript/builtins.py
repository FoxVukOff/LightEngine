import math

from .runtime import Range, dump, to_str, truthy, type_name, iterate
from engine.mathx import Vec, Color, rgb, clamp, lerp, lerp_angle, wrap_angle


def make_range(*a):
    if len(a) == 1:
        return Range(0, a[0])
    if len(a) == 2:
        return Range(a[0], a[1])
    return Range(a[0], a[1], a[2])


def make_globals(ctx):
    g = {
        'print': ctx.log,
        'say': ctx.log,
        'dump': dump,
        'type': type_name,
        'str': to_str,
        'int': lambda v=0: int(v),
        'float': lambda v=0.0: float(v),
        'bool': truthy,
        'vec2': lambda x=0.0, y=None: Vec(x, y),
        'v2': lambda x=0.0, y=None: Vec(x, y),
        'color': rgb,
        'rgb': rgb,
        'mix': lambda a, b, t: a.mix(b, t),
        'abs': abs,
        'sign': lambda v: (v > 0) - (v < 0),
        'min': min,
        'max': max,
        'round': lambda v, d=0: math.floor(v * 10 ** d + 0.5) / 10 ** d if d else math.floor(v + 0.5),
        'floor': math.floor,
        'ceil': math.ceil,
        'sqrt': lambda v: math.sqrt(v) if v >= 0 else 0.0,
        'pow': math.pow,
        'exp': math.exp,
        'log': lambda v: math.log(v) if v > 0 else 0.0,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': lambda v: math.asin(clamp(v, -1.0, 1.0)),
        'acos': lambda v: math.acos(clamp(v, -1.0, 1.0)),
        'atan': math.atan,
        'atan2': math.atan2,
        'deg': math.degrees,
        'rad': math.radians,
        'hypot': math.hypot,
        'clamp': clamp,
        'lerp': lerp,
        'lerp_angle': lerp_angle,
        'wrap_angle': wrap_angle,
        'dist': lambda a, b: a.dist_to(b),
        'len': lambda v: len(v) if not isinstance(v, (Vec, Color)) else len(iterate(v)),
        'range': make_range,
        'list': list,
        'dict': dict,
        'keys': lambda d: list(d.keys()),
        'values': lambda d: list(d.values()),
        'items': lambda d: [list(kv) for kv in d.items()],
        'has': lambda c, v: v in (c if not isinstance(c, (list, str, dict, Range)) else iterate(c)),
        'push': lambda l, v: (l.append(v), l)[1],
        'pop': lambda l, i=-1: l.pop(i),
        'sort': lambda l, rev=False: sorted(l, reverse=rev),
        'count': lambda l, v: sum(1 for x in iterate(l) if x == v),
        'rand': ctx.rand,
        'randi': ctx.randi,
        'choice': ctx.choice,
        'shuffle': ctx.shuffle,
        'chance': ctx.chance,
        'time': ctx.time,
        'frame': ctx.frame,
        'dt': ctx.dt,
        'screen': ctx.screen,
        'center': ctx.center,
        'input': ctx.input,
    }
    return g


def help_text():
    keys = [
        ('let / const', 'РѕР±СЉСЏРІР»РµРЅРёРµ РїРµСЂРµРјРµРЅРЅРѕР№, const РЅРµ РїРµСЂРµРїСЂРёСЃРІР°РёРІР°РµС‚СЃСЏ'),
        ('func f(a, b=1)', 'С„СѓРЅРєС†РёСЏ, return РёР»Рё -> РґР»СЏ РІС‹С…РѕРґР°'),
        ('if / elif / else, unless', 'РІРµС‚РєРё, unless СЌС‚Рѕ if not'),
        ('while, for x in list, repeat n', 'С†РёРєР»С‹, repeat -1 Р±РµСЃРєРѕРЅРµС‡РЅС‹Р№'),
        ('a if c else b РёР»Рё c ? a : b', 'С‚РµСЂРЅР°СЂРЅРёРє'),
        ('a ?? b, a?.b, a |> f()', 'РґРµС„РѕР»С‚, Р±РµР·РѕРїР°СЃРЅС‹Р№ РґРѕСЃС‚СѓРї, РїР°Р№Рї'),
        ('a..b, a..b..c', 'РґРёР°РїР°Р·РѕРЅС‹'),
        ('// РєРѕРјРјРµРЅС‚Р°СЂРёР№', 'РєРѕРјРјРµРЅС‚Р°СЂРёР№ РґРѕ РєРѕРЅС†Р° СЃС‚СЂРѕРєРё'),
    ]
    out = ['СЃР»РѕРІР°:', '']
    for k, v in keys:
        out.append('  %-28s %s' % (k, v))
    out += ['', 'math: sin cos tan atan2 sqrt abs min max round floor ceil clamp lerp lerp_angle deg rad',
            'vec: vec2(x,y) + - * / .len() .normed() .angle() .rot() .dist_to() .to()',
            'color: rgb(r,g,b,a) 0xff8800 .mix() .to_hex()',
            'random: rand(a,b) randi(a,b) choice(list) shuffle(list) chance(p)',
            'СЃРѕР±С‹С‚РёСЏ: on_start on_update(dt) on_draw(g) on_click(pos) on_key(key) on_collide(other)',
            'self: x y pos vel angle scale spin z alive scene input time dt frame screen',
            'self: say() kill() clone() get(name) find(name) add(type,name) move() set_pos() play()',
            'РІСЃС‚СЂРѕРµРЅРЅС‹Рµ СЃРїРёСЃРєРё: keys values items has push pop sort count len range',
            'print() РґР»СЏ РєРѕРЅСЃРѕР»Рё СЂРµРґР°РєС‚РѕСЂР°, СЂР°Р±РѕС‚Р°РµС‚ Рё РІ РёРіСЂРµ']
    return '\n'.join(out)
