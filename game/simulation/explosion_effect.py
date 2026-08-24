class ExplosionEffect:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.life = 260

    def update(self, dt):
        self.life -= dt

    def is_alive(self):
        return self.life > 0
