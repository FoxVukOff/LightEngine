# пример: рисование в on_draw
# свет, который дышит, и рамка вокруг экрана

let t = 0.0

on_start:
    self.say("draw demo")

on_update(dt):
    t = t + dt

on_draw(g):
    # радиальное свечение
    let r = 160 + sin(t * 2) * 40
    g.glow(self.pos.x, self.pos.y, r, rgb(255, 210, 120), 1.4)

    # круги по спирали
    for i in 0..12:
        let a = t + i * 0.5
        let rad = 40 + i * 8
        let p = self.pos + v2(cos(a), sin(a)) * rad
        g.circle(p.x, p.y, 4 + i * 0.6, rgb(120, 220, 255, 0.7))

    # полоска внизу экрана
    let w = 200 + sin(t * 3) * 60
    g.rect(self.pos.x, self.pos.y + 100, w, 8, rgb(255, 120, 90), true)

    # текст
    g.text(self.pos.x, self.pos.y - 120, "t = " + str(round(t, 1)), rgb(240, 240, 250), 16, ox=0.5)
