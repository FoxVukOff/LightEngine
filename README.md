# LightEngine

2д игровой движок на Python + PyQt6 со своим скриптовым языком **LightScript**.
Редактор сцен встроенный: узлы, инспектор, канвас, консоль языка, play прямо в редакторе,
сборка игры в отдельный exe.

автор: **FoxVukOff**

## запуск

```
python main.py                 # редактор
python main.py scenes/main.lscene
run.bat                        # то же самое на windows
```

первый запуск создаёт `project.json`, `assets/`, `scenes/`, `dist/` и стартовую сцену.

## сборка

```
build\build_exe.bat            # сам движок -> build\dist\LightEngine.exe
build\build_exe.bat --onedir   # папкой, старт быстрее
build\build_exe.bat --console  # с консолью, видно print и ошибки

build\build_game.bat путь_к_проекту имя_игры
python build\build_game.py . --name mygame
```

в редакторе: `file -> build game exe...` (ctrl+B) или `run -> run game in window`.
Нужен `pip install pyinstaller`.

## проекты

```
проект/
  project.json     имя, входная сцена, размер окна, цвет фона
  scenes/          *.lscene - сцены, json в читаемом виде
  assets/          текстуры (png jpg bmp svg) и звуки (wav ogg mp3)
  scripts/         текстовые заметки и куски скриптов
  dist/            собранные exe игры
```

`file -> new project` / `open project`. У каждого проекта свои ассеты и свой dist.

## узлы

| тип | что это |
| --- | --- |
| `Node2D` | пустой контейнер с трансформом |
| `Sprite` | текстура из assets, цвет, якоря, flip |
| `Rect` | прямоугольник, заливка или рамка |
| `Circle` | круг |
| `Label` | текст |
| `Area` | невидимая зона: ввод и столкновения |
| `Camera2D` | камера, зум, слежение за узлом |
| `Light2D` | аддитивное свечение |

у каждого узла: `pos`, `vel`, `gravity`, `angle`, `spin`, `scale`, `z`, `visible`, `script`.
Позиция детей локальная, `wpos()` даёт мировую.

## LightScript

похож на python, но с сахаром и без `class` (есть `func` и события-функции).

```
let hp = 100
const MAX = 3
x = 5                        # можно и без let

func heal(v, mult=1.0):
    hp = hp + v * mult
    return hp

on_start:
    self.say("hp is ", hp)

on_update(dt):
    if input.down("right"):
        self.pos = self.pos + v2(300, 0) * dt
    elif input.down("left"):
        self.pos = self.pos + v2(-300, 0) * dt
    unless hp <= 0:
        hp -= 1

on_draw(g):
    g.rect(self.pos.x, self.pos.y, hp, 12, rgb(90, 220, 140))
```

отличия от python:

* `func` и `def`, плюс голые события `on_start:` / `on_update(dt):` без `func`
* `let` / `const`, но присваивать можно и без `let`
* `unless` = `if not`, `repeat n` (и `repeat -1` как бесконечный цикл), `pass`
* тернарник в двух видах: `a if c else b` и `c ? a : b`
* `a ?? b` - дефолт, `a?.b` - безопасный доступ, `a |> f(x)` - пайп
* `a..b` и `a..b..c` - диапазоны, правая граница не включается как в `range`
* `//` и `#` комментарии, `\` перенос строки
* `"""..."""` многострочные строки
* `for k, v in items(dict)` - два значения сразу

события: `on_start`, `on_update(dt)`, `on_draw(g)`, `on_click(pos)`, `on_key(key)`,
`on_collide(other)`, `on_collide_exit(other)`, `on_timer(name)`.

переменные верхнего уровня живут между кадрами, поэтому счётчики удобно держать там.

### self

`x y pos vel gravity angle spin scale z visible alive name width height scene input`
`time dt frame screen center res node`

методы: `say() kill() clone() add(type,name) remove(other) get(name) find(name)`
`move() set_pos() set_vel() look_at() dist_to() count_children() timer(name,sec) play(name)`
`rect() circle() line() text() sprite() poly() glow()` - рисуют в текущем кадре

### функции

`print sin cos tan atan2 sqrt abs min max round floor ceil clamp lerp lerp_angle deg rad`
`vec2 v2 rgb color mix len range list dict keys values items has push pop sort count`
`rand randi choice shuffle chance time frame dt screen center input`

`vec2`: `+ - * / .len() .normed() .angle() .rot() .dist_to() .to(other,t)`
`color`: `rgb(r,g,b,a) 0xff8800 .mix() .to_hex()`

## горячие клавиши

| | |
| --- | --- |
| `F5` / `F6` | play / stop |
| `space` + мышь | панорамирование, колесо - зум |
| `ctrl+d` / `del` | дублировать / удалить |
| `ctrl+s` / `ctrl+o` | сохранить / открыть сцену |
| `ctrl+b` | собрать игру в exe |
| `ctrl+shift+f` | вписать всю сцену в экран |
| `f` | навести камеру на выбранный узел |
| стрелки | сдвиг на грид, `shift` - на пиксель |
| правая кнопка | меню: добавить узел, дублировать, удалить, z |

## тесты

```
python tests\run_tests.py
python tests\run_editor_test.py
```

## структура

```
engine/     mathx node scene game graphics resources input project serialize gameapp
lscript/    lexer parser runtime builtins
editor/     mainwindow canvas hierarchy inspector console
build/      build_exe.py build_game.py pack.py
```
