# пример: движение мышью с инерцией
# вешай на Area, в инспекторе поставь w и h побольше

let vx = 0.0
let vy = 0.0

on_start:
    self.say("follow the mouse")

on_update(dt):
    let target = input.mouse
    let d = self.pos.angle_to(target)
    let dist = self.pos.dist_to(target)

    if dist > 40:
        vx = lerp(vx, target.x - self.pos.x, 0.1)
        vy = lerp(vy, target.y - self.pos.y, 0.1)
    else:
        vx = vx * 0.9
        vy = vy * 0.9

    self.pos = self.pos + v2(vx, vy) * dt
    self.angle = lerp_angle(self.angle, d, 0.2)

    if input.pressed("space"):
        self.say("clicked at ", target)
        self.color = rgb(255, 180, 60)
    else:
        self.color = self.color.mix(rgb(90, 200, 255), 0.05)
