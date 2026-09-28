# LightScript

язык движка LightEngine. синтаксис как у python, но короче и с сахаром под игры.
нет `class`, зато есть события узлов, векторы, цвета и таймеры.

## объявления

```lightscript
let hp = 100
const MAX = 3
x = 5                    # let можно опускать
n = n + 1                # при первом обращении переменная создаётся сама
```

`const` запрещает переприсваивание, но не проверяется при `=`, только при `let`.

## функции

```lightscript
func heal(v, mult=1.0):
    return hp + v * mult

func step()              # без аргументов
    pass
```

`def` работает как `func`. тело блока отступом, можно в одну строку через двоеточие:

```lightscript
if hp < 0: self.kill()
```

## события

события пишутся без `func`, имя и скобки как у обычной функции:

```lightscript
on_start:
    self.say("готов")

on_update(dt):
    self.angle = self.angle + 90 * dt

on_draw(g):
    g.circle(self.pos.x, self.pos.y, 20, rgb(255, 120, 60))

on_click(pos):
    self.say("клик ", pos)

on_key(key):
    if key == "r":
        self.pos = v2(0, 0)

on_collide(other):
    self.say("столкнулся с ", other.name)

on_collide_exit(other):
    pass

on_timer(name):
    if name == "wave":
        self.add("Area", "enemy")
```

таймер ставится из скрипта:

```lightscript
self.timer("wave", 2.0)
```

переменные верхнего уровня живут между кадрами, счётчики удобно держать там:

```lightscript
let score = 0

on_update(dt):
    score = score + dt
```

## ветки и циклы

```lightscript
if a > b:
    say_win()
elif a == b:
    say_draw()
else:
    say_lose()

unless hp > 0:
    self.kill()

while n < 10:
    n = n + 1

for i in 0..10:          # 0..10 это 0 1 2 ... 9, правая граница не включается
    total = total + i

for k, v in items({"hp": 10}):
    print(k, v)

repeat 5:
    spawn()

repeat -1:               # бесконечный цикл
    wait_frame()
```

есть `break`, `continue`, `pass`.

## выражения

| что | как |
| --- | --- |
| тернарник | `a if c else b` или `c ? a : b` |
| дефолт | `a ?? b` |
| безопасный доступ | `a?.b` |
| пайп | `x |> sqrt()`, `5 |> clamp(0, 3)` |
| диапазон | `0..10`, `10..0..-1` |
| логика | `and`, `or`, `not`, `!` |
| сравнение | `==` `!=` `<` `<=` `>` `>=` `in` |
| арифметика | `+` `-` `*` `/` `//` `%` `**` |
| присваивание | `=` `+=` `-=` `*=` `/=` `//=` `%=` `**=` |
| перенос строки | `\` в конце строки |

`if`, `true`, `false`, `null` работают как в python, регистр не важен:
`True`, `False`, `None` тоже понимаются.

## типы

```lightscript
let v = v2(10, 20)               # вектор, есть ещё vec2()
let c = rgb(255, 120, 60)        # цвет, есть color(), числа 0..255
let c2 = rgb(0xff8040)           # цвет из числа
let s = "строка"
let s2 = """
многострочная
строка
"""
let l = [1, 2, 3]
let d = {"hp": 10, "mp": 3}
let r = 0..10
```

вектор:

```lightscript
v.len() v.len2() v.normed() v.angle() v.rot(45) v.round()
v.dist_to(other) v.to(other, 0.5) v.dot(other) v.cross(other)
v + w   v - w   v * 2   v / 2   -v
v.x    v.y
```

цвет:

```lightscript
c.mix(other, 0.5) c.with_alpha(0.5) c.to_hex() c * 0.5
c.r   c.g   c.b   c.a
```

у объектов движка поля читаются без скобок, а методы вызываются: `self.pos`,
`self.pos.x`, но `self.find("body")`. если имя совпадает с полем и с методом,
побеждает поле.

## self

свойства узла:

```lightscript
self.x self.y self.pos self.vel self.gravity
self.angle self.spin self.scale self.z self.visible
self.name self.alive self.width self.height
```

окружение:

```lightscript
self.scene self.input self.time self.dt self.frame
self.screen self.center self.res self.node
```

методы:

```lightscript
self.say("текст в консоль")
self.move(10, 0) self.set_pos(0, 0) self.set_vel(100, 0)
self.look_at(100, 0) self.dist_to(other)
self.kill() self.clone() self.add("Area", "enemy") self.count_children()
self.get("player") self.find("body") self.remove(other)
self.play("hit") self.timer("wave", 2.0)
```

рисование из скрипта, координаты в мире:

```lightscript
self.rect(x, y, w, h, color, fill)
self.circle(x, y, r, color, fill)
self.line(x0, y0, x1, y1, color, width)
self.text(x, y, "строка", color, size)
self.sprite("hero.png", x, y)
```

те же методы есть у `g` в `on_draw(g)`, плюс `g.poly`, `g.glow`, `g.gradient_rect`, `g.clip`.

## встроенные функции

| группа | функции |
| --- | --- |
| математика | `sin` `cos` `tan` `atan2` `asin` `acos` `atan` `sqrt` `pow` `exp` `log` `abs` `sign` `min` `max` `round` `floor` `ceil` `deg` `rad` `hypot` |
| интерполяция | `clamp` `lerp` `lerp_angle` `wrap_angle` `mix` `dist` |
| списки | `len` `range` `list` `dict` `keys` `values` `items` `has` `push` `pop` `sort` `count` |
| случайность | `rand` `randi` `choice` `shuffle` `chance` |
| время | `time` `frame` `dt` `screen` `center` |
| вывод | `print` `say` `dump` `type` `str` `int` `float` `bool` |

`in` работает со списками, словарями, строками и диапазонами:

```lightscript
if "hp" in d:
    print(d.hp)
```

## ввод

```lightscript
input.axis()             # вектор из стрелок и wasd
input.down("right")      # удерживается
input.pressed("space")   # нажата в этом кадре
input.up_edge("shift")   # отпущена в этом кадре
input.mouse              # позиция мыши в мире
input.mouse_delta()
input.wheel
input.buttons
```

имена клавиш: `left` `right` `up` `down` `space` `enter` `escape` `tab` `shift` `ctrl` `alt`,
буквы `a`-`z`, цифры `0`-`9`, `f1`-`f12`.

## комментарии

```lightscript
# комментарий до конца строки
// тоже комментарий
```

## примеры

готовые скрипты лежат в папке `examples`:

| файл | что показывает |
| --- | --- |
| `follow_mouse.ls` | движение за мышью с инерцией |
| `spawner.ls` | таймеры, спавн врагов, столкновения |
| `on_draw.ls` | рисование в `on_draw`, свечение, спирали |
