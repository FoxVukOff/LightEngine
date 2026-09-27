# пример: спавн врагов и подсчёт очков
# вешай на Area, который следит за игроком

let spawn_cd = 0.0
let score = 0
let target = null

on_start:
    self.timer("wave", 2.0)
    self.say("spawner started")

on_update(dt):
    spawn_cd -= dt
    if input.pressed("left"):
        score = score + 1
        self.say("score: ", score)

on_timer(name):
    if name == "wave":
        target = self.get("player")
        if target == null:
            return
        let e = self.add("Area", "enemy")
        let a = rand(0, 6.28)
        e.pos = self.pos + v2(cos(a), sin(a)) * 220
        e.w = 24
        e.h = 24
        e.color = rgb(220, 70, 90)
        e.script = """
on_update(dt):
    let p = self.get("player")
    if p == null:
        self.kill()
        return
    let dir = self.pos.angle_to(p.pos)
    self.angle = dir
    self.pos = self.pos + v2(cos(dir), sin(dir)) * 90 * dt

on_collide(other):
    if other.name == "player":
        self.kill()
        self.say("hit")
"""
        self.say("enemy spawned, total ", self.count_children())
