"""
neon_geometry_wars_shop_full.py
Neon Geometry Wars — full single-file version
- Shop opens with P (pauses game)
- Exponential ship pricing
- PowerUp defined
- Keeps neon look from prior version
"""

import pygame
import random
import math
import sys
from collections import deque

pygame.init()

# ---------------- Constants & Colors (match old neon look) ----------------
WIDTH = 900
HEIGHT = 700
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 100)
ORANGE = (255, 165, 0)
PURPLE = (200, 50, 255)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
GRAY = (150, 150, 150)
DARK_GRID = (20, 20, 40)
LIME = (0, 255, 0)

pygame.font.init()
FONT_SMALL = pygame.font.Font(None, 20)
FONT_MED = pygame.font.Font(None, 28)
FONT_LARGE = pygame.font.Font(None, 36)
FONT_XL = pygame.font.Font(None, 56)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Geometry Wars (Shop & Unique Bosses)")
clock = pygame.time.Clock()

# ---------------- Utility functions ----------------
def clamp(v, a, b):
    return max(a, min(b, v))

def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def neon_text(s, font, color, glow_color=None):
    base = font.render(s, True, color)
    if not glow_color:
        return base
    glow_surf = pygame.Surface((base.get_width() + 28, base.get_height() + 28), pygame.SRCALPHA)
    # soft glow layers
    for i, alpha in enumerate((40, 20, 10), start=1):
        tmp = font.render(s, True, glow_color)
        tmp.set_alpha(alpha)
        glow_surf.blit(tmp, (14 - i, 14 - i))
    glow_surf.blit(base, (14, 14))
    return glow_surf

# ---------------- Particle class (for explosions/trails) ----------------
class Particle:
    def __init__(self, x, y, color, life=30, size=None):
        self.x = x
        self.y = y
        a = random.uniform(0, 2 * math.pi)
        s = random.uniform(1.8, 5.0)
        self.vx = math.cos(a) * s
        self.vy = math.sin(a) * s
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size if size is not None else random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = clamp(int(255 * (self.life / self.max_life)), 0, 255)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, self.color + (alpha,), (self.size, self.size), self.size)
        surf.blit(s, (self.x - self.size, self.y - self.size))

# ---------------- Bullet class ----------------
class Bullet:
    def __init__(self, x, y, angle, speed=10, owner='player', damage=1.0, homing=False):
        self.x = x
        self.y = y
        self.angle = angle
        rad = math.radians(angle)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        self.speed = speed
        self.lifetime = 70
        self.radius = 3 if owner == 'player' else 4
        self.owner = owner
        self.damage = damage
        self.homing = homing

    def update(self, enemies=None):
        if self.homing and enemies:
            # steer to closest enemy
            best = None; best_d = 1e9
            for e in enemies:
                d = distance(self.x, self.y, e.x, e.y)
                if d < best_d:
                    best_d = d; best = e
            if best:
                target = math.degrees(math.atan2(best.y - self.y, best.x - self.x))
                diff = (target - self.angle + 180) % 360 - 180
                self.angle += diff * 0.12
                rad = math.radians(self.angle)
                self.vx = math.cos(rad) * self.speed
                self.vy = math.sin(rad) * self.speed
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        # wrap
        if self.x < 0: self.x = WIDTH
        elif self.x > WIDTH: self.x = 0
        if self.y < 0: self.y = HEIGHT
        elif self.y > HEIGHT: self.y = 0

    def draw(self, surf):
        col = YELLOW if self.homing else (WHITE if self.owner == 'player' else MAGENTA)
        # glow rings
        for w in (6, 3):
            pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.radius + w, 1)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.radius)

    def is_alive(self):
        return self.lifetime > 0

# ---------------- Geometric enemy (normal) ----------------
class GeometricEnemy:
    def __init__(self, x, y, shape_type, size, scale=1.0):
        self.x = x
        self.y = y
        self.shape_type = shape_type
        self.size = size
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        if shape_type == 'triangle':
            self.sides = 3; self.color = RED; self.speed = 2.0; self.health = 1; self.coin = 5
        elif shape_type == 'square':
            self.sides = 4; self.color = ORANGE; self.speed = 1.6; self.health = 2; self.coin = 10
        elif shape_type == 'pentagon':
            self.sides = 5; self.color = YELLOW; self.speed = 1.1; self.health = 3; self.coin = 20
        else:  # hexagon
            self.sides = 6; self.color = GREEN; self.speed = 0.8; self.health = 4; self.coin = 35
        self.speed *= scale
        ang = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(ang) * self.speed
        self.vy = math.sin(ang) * self.speed

    def update(self, px, py, diff=1.0):
        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy)
        if d > 0:
            self.vx += (dx / d) * 0.03 * diff
            self.vy += (dy / d) * 0.03 * diff
        s = math.hypot(self.vx, self.vy)
        cap = self.speed * (1 + diff * 0.12)
        if s > cap:
            self.vx = (self.vx / s) * cap
            self.vy = (self.vy / s) * cap
        self.x += self.vx; self.y += self.vy
        self.angle += self.rotation_speed
        # wrap with padding
        if self.x < -60: self.x = WIDTH + 60
        if self.x > WIDTH + 60: self.x = -60
        if self.y < -60: self.y = HEIGHT + 60
        if self.y > HEIGHT + 60: self.y = -60

    def hit(self, dmg=1.0):
        self.health -= dmg
        return self.health <= 0

    def split(self):
        if self.size > 14:
            new = []
            for _ in range(2):
                a = random.uniform(0, 360); r = math.radians(a)
                nx = self.x + math.cos(r) * 18; ny = self.y + math.sin(r) * 18
                new.append(GeometricEnemy(nx, ny, self.shape_type, max(10, self.size // 2)))
            return new
        return []

    def draw(self, surf):
        pts = []
        for i in range(self.sides):
            r = math.radians(self.angle + i * (360 / self.sides))
            pts.append((self.x + math.cos(r) * self.size, self.y + math.sin(r) * self.size))
        # neon multi-outline
        for w in (6, 3, 1):
            pygame.draw.polygon(surf, self.color, pts, w)

# ---------------- PowerUp class (explicitly defined as requested) ----------------
class PowerUp:
    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype  # 'spread', 'rapid', 'life', 'shield'
        self.lifetime = 360
        self.radius = 14
        if self.type == 'spread': self.color = YELLOW
        elif self.type == 'rapid': self.color = MAGENTA
        elif self.type == 'life': self.color = GREEN
        elif self.type == 'shield': self.color = CYAN
        else: self.color = WHITE

    def update(self):
        self.lifetime -= 1

    def is_alive(self):
        return self.lifetime > 0

    def draw(self, surf):
        pulse = abs((self.lifetime % 40) - 20) / 20
        rad = int(self.radius + pulse * 5)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), rad, 2)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), rad - 6, 1)

# ---------------- Player Ship class and ship definitions ----------------
SHIP_BASES = [
    # name, base_cost (will be exponentiated), stats dictionary
    ("Scout", 0, {"speed": 8.5, "acc": 0.36, "shoot_delay": 10, "bullet_speed": 12, "bullet_dmg": 1.0, "desc": "Fast, nimble, light damage"}),
    ("Fighter", 1, {"speed": 7.5, "acc": 0.32, "shoot_delay": 9, "bullet_speed": 12, "bullet_dmg": 1.3, "desc": "Balanced"}),
    ("Destroyer", 2, {"speed": 6.3, "acc": 0.26, "shoot_delay": 12, "bullet_speed": 10, "bullet_dmg": 2.2, "desc": "Heavy damage"}),
    ("Blazer", 3, {"speed": 7.2, "acc": 0.30, "shoot_delay": 6, "bullet_speed": 14, "bullet_dmg": 1.1, "desc": "Rapid spread"}),
    ("Nova", 4, {"speed": 6.0, "acc": 0.24, "shoot_delay": 11, "bullet_speed": 10, "bullet_dmg": 3.0, "desc": "Explosive hits"}),
    ("Vector", 5, {"speed": 8.0, "acc": 0.40, "shoot_delay": 8, "bullet_speed": 13, "bullet_dmg": 1.4, "desc": "High mobility & accuracy"}),
    ("Dread", 6, {"speed": 5.6, "acc": 0.22, "shoot_delay": 14, "bullet_speed": 9, "bullet_dmg": 4.2, "desc": "Massive damage, slow"}),
]

# exponential pricing base
PRICE_BASE = 300  # base multiplier for exponent
PRICE_MULT = 2.2  # exponential factor: cost = base * (mult^tier)
def ship_price(tier):
    # tier 0 (Scout) free (0 cost), others exponential
    if tier <= 0: return 0
    return int(PRICE_BASE * (PRICE_MULT ** (tier - 1)))

SHIP_DEFS = {}
for name, tier, stats in SHIP_BASES:
    cost = ship_price(tier)
    SHIP_DEFS[name] = dict(cost=cost, tier=tier, **stats)

class Player:
    def __init__(self, ship_name="Scout"):
        self.ship_name = ship_name
        self.apply_ship(ship_name)
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.vx = 0
        self.vy = 0
        self.radius = 12
        self.lives = 3
        self.invulnerable = 0
        self.weapon_type = 'normal'
        self.weapon_timer = 0
        self.shoot_cooldown = 0
        self.angle = 0  # facing right

    def apply_ship(self, name):
        s = SHIP_DEFS[name]
        self.speed = s["speed"]
        self.acc = s["acc"]
        self.shoot_delay = s["shoot_delay"]
        self.bullet_speed = s["bullet_speed"]
        self.bullet_dmg = s["bullet_dmg"]
        self.desc = s["desc"]
        # color by tier (approximate)
        tier = s["tier"]
        if name == "Scout":
            self.color = CYAN
        elif tier <= 1:
            self.color = CYAN
        elif tier == 2:
            self.color = ORANGE
        elif tier == 3:
            self.color = MAGENTA
        elif tier == 4:
            self.color = PURPLE
        elif tier == 5:
            self.color = BLUE
        else:
            self.color = RED
        self.ship_name = name

    def rotate(self, direction):
        self.angle += direction * 5

    def thrust(self):
        rad = math.radians(self.angle)
        self.vx += math.cos(rad) * self.acc
        self.vy += math.sin(rad) * self.acc
        s = math.hypot(self.vx, self.vy)
        if s > self.speed:
            self.vx = (self.vx / s) * self.speed
            self.vy = (self.vy / s) * self.speed

    def update(self):
        self.vx *= 0.985
        self.vy *= 0.985
        self.x += self.vx; self.y += self.vy
        if self.x < 0: self.x = WIDTH
        if self.x > WIDTH: self.x = 0
        if self.y < 0: self.y = HEIGHT
        if self.y > HEIGHT: self.y = 0
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.invulnerable > 0: self.invulnerable -= 1
        if self.weapon_timer > 0: self.weapon_timer -= 1
        else: self.weapon_type = 'normal'

    def can_shoot(self):
        return self.shoot_cooldown == 0

    def shoot(self):
        self.shoot_cooldown = max(1, int(self.shoot_delay))

    def draw(self, surf):
        if getattr(self, "invulnerable", 0) > 0 and (self.invulnerable // 6) % 2 == 0:
            return
        rad = math.radians(self.angle)
        front_x = self.x + math.cos(rad) * (self.radius + 4)
        front_y = self.y + math.sin(rad) * (self.radius + 4)
        back_left_x = self.x + math.cos(rad + 2.6) * self.radius
        back_left_y = self.y + math.sin(rad + 2.6) * self.radius
        back_right_x = self.x + math.cos(rad - 2.6) * self.radius
        back_right_y = self.y + math.sin(rad - 2.6) * self.radius
        color = self.color
        if self.weapon_type == 'spread': color = YELLOW
        if self.weapon_type == 'rapid': color = MAGENTA
        # neon polygon strokes
        for w in (6, 4, 2):
            pygame.draw.polygon(surf, color, [(front_x, front_y), (back_left_x, back_left_y), (self.x, self.y), (back_right_x, back_right_y)], w)
        # thruster
        if abs(self.vx) > 0.5 or abs(self.vy) > 0.5:
            back_x = self.x - math.cos(rad) * self.radius * 0.9
            back_y = self.y - math.sin(rad) * self.radius * 0.9
            pygame.draw.circle(surf, ORANGE, (int(back_x), int(back_y)), 4)



# ---------------- Boss base and unique bosses ----------------
class BossBase:
    def __init__(self, index):
        self.index = index
        self.t = 0
        self.x = WIDTH // 2
        self.y = -150
        self.phase = 0
        self.dead = False
        # default visuals
        self.sides = 10
        self.size = 80 + 8 * index
        self.color = PURPLE
        self.health = 120 + index * 50
        self.max_health = self.health

    def start(self):
        self.spawned = True

    def update(self, game):
        self.t += 1

    def hit(self, dmg):
        self.health -= dmg
        return self.health <= 0

    def draw(self, surf):
        pts = []
        for i in range(self.sides):
            r = math.radians(self.t * 0.6 + i * (360 / self.sides))
            pts.append((self.x + math.cos(r) * self.size, self.y + math.sin(r) * self.size))
        for w in (8, 4):
            pygame.draw.polygon(surf, self.color, pts, w)
        # healthbar
        ratio = clamp(self.health / max(1, self.max_health), 0, 1)
        w = 220; h = 12
        pygame.draw.rect(surf, (20, 20, 20), (self.x - w / 2, self.y - self.size - 34, w, h))
        pygame.draw.rect(surf, RED, (self.x - w / 2, self.y - self.size - 34, w, h))
        pygame.draw.rect(surf, LIME, (self.x - w / 2, self.y - self.size - 34, w * ratio, h))

# Hexagon Sentinel - radial + spin bullets
class HexagonSentinel(BossBase):
    def __init__(self, idx):
        super().__init__(idx)
        self.sides = 6
        self.size = 70 + idx * 8
        self.color = MAGENTA
        self.health = 120 + idx * 60
        self.max_health = self.health

    def update(self, game):
        super().update(game)
        if self.y < HEIGHT // 3:
            self.y += 1.6 + self.index * 0.05
        # radial burst
        if self.t % max(40, 120 - self.index * 6) == 0:
            n = 8 + self.index
            for i in range(n):
                ang = (360 / n) * i + random.uniform(-6, 6)
                speed = 5 + min(6, self.index * 0.6)
                game.boss_bullets.append(Bullet(self.x, self.y, ang, speed, owner='boss', damage=1.0))
        # spin stream
        if self.t % max(6, 12 - self.index) == 0:
            angle = (self.t * 2) % 360
            for off in (-3, 0, 3):
                game.boss_bullets.append(Bullet(self.x, self.y, angle + off, 10 + 0.2 * self.index, owner='boss', damage=1.0))

# Vortex Eye - teleports & homing clusters
class VortexEye(BossBase):
    def __init__(self, idx):
        super().__init__(idx)
        self.sides = 8
        self.size = 60 + idx * 7
        self.color = PURPLE
        self.health = 140 + idx * 60
        self.max_health = self.health
        self.tp_timer = max(90, 180 - idx * 8)
        self.cluster_timer = max(30, 60 - idx * 3)

    def update(self, game):
        super().update(game)
        if self.t % 6 == 0:
            dx = game.player.x - self.x; dy = game.player.y - self.y
            d = math.hypot(dx, dy)
            if d > 0:
                self.x += (dx / d) * 0.6; self.y += (dy / d) * 0.6
        if self.t % max(1, self.cluster_timer) == 0:
            for _ in range(2 + self.index // 2):
                ang = random.uniform(0, 360)
                game.boss_bullets.append(Bullet(self.x, self.y, ang, 6 + 0.2 * self.index, owner='boss', damage=1.0, homing=True))
        if self.t % self.tp_timer == 0:
            self.x = clamp(game.player.x + random.randint(-120, 120), 80, WIDTH - 80)
            self.y = clamp(game.player.y + random.randint(-120, 120), 80, HEIGHT - 80)
            for off in (-4, -2, 0, 2, 4):
                angle_to_player = math.degrees(math.atan2(game.player.y - self.y, game.player.x - self.x))
                game.boss_bullets.append(Bullet(self.x, self.y, angle_to_player + off * 6, 11, owner='boss', damage=1.1))

# Spiral Core - spirals and charge beam
class SpiralCore(BossBase):
    def __init__(self, idx):
        super().__init__(idx)
        self.sides = 12
        self.size = 80 + idx * 6
        self.color = ORANGE
        self.health = 160 + idx * 70
        self.max_health = self.health
        self.charge = 0

    def update(self, game):
        super().update(game)
        self.x = WIDTH // 2 + math.cos(self.t * 0.02) * (50 + self.index * 6)
        self.y = HEIGHT // 3 + math.sin(self.t * 0.02) * (30 + self.index * 4)
        n = 10 + self.index * 2
        if self.t % max(4, 10 - self.index) == 0:
            base = (self.t * 6) % 360
            for i in range(3):
                ang = base + i * (360 / 3)
                for j in range(n):
                    game.boss_bullets.append(Bullet(self.x, self.y, ang + j * (360 / n) + j * 0.6, 5 + j * 0.02, owner='boss', damage=0.9))
        if self.t % max(200, 300 - self.index * 12) == 0:
            self.charge = 60
        if self.charge > 0:
            if self.charge % 12 == 0:
                angle_to_player = math.degrees(math.atan2(game.player.y - self.y, game.player.x - self.x))
                for off in (-8, -4, 0, 4, 8):
                    game.boss_bullets.append(Bullet(self.x, self.y, angle_to_player + off, 16 + self.index * 0.3, owner='boss', damage=2.0))
            self.charge -= 1

# Shard King - spawns shards and dashes
class ShardKing(BossBase):
    def __init__(self, idx):
        super().__init__(idx)
        self.sides = 9
        self.size = 60 + idx * 7
        self.color = BLUE
        self.health = 150 + idx * 60
        self.max_health = self.health
        self.spawn_timer = max(60, 140 - idx * 6)
        self.dash_timer = max(50, 90 - idx * 4)

    def update(self, game):
        super().update(game)
        if self.t % 8 == 0:
            self.x += math.cos(self.t * 0.03) * (1 + self.index * 0.02)
            self.y += math.sin(self.t * 0.03) * (1 + self.index * 0.02)
        if self.t % max(40, self.spawn_timer) == 0:
            for _ in range(1 + self.index // 3):
                offx = random.uniform(-40, 40); offy = random.uniform(-40, 40)
                game.enemies.append(GeometricEnemy(self.x + offx, self.y + offy, random.choice(['triangle', 'square']), random.randint(12, 18)))
        if self.t % max(60, self.dash_timer) == 0:
            dx = game.player.x - self.x; dy = game.player.y - self.y
            d = math.hypot(dx, dy)
            if d > 0:
                nx = self.x + (dx / d) * 160; ny = self.y + (dy / d) * 160
                self.x, self.y = nx, ny
                for i in range(12 + self.index * 2):
                    game.boss_bullets.append(Bullet(self.x, self.y, i * (360 / (12 + self.index * 2)) + random.uniform(-6, 6), 7 + 0.1 * self.index, owner='boss', damage=1.1))

# Star Forge - summons minions and star spirals with phases
class StarForge(BossBase):
    def __init__(self, idx):
        super().__init__(idx)
        self.sides = 7
        self.size = 68 + idx * 6
        self.color = LIME
        self.health = 180 + idx * 80
        self.max_health = self.health
        self.phase_timer = 0

    def update(self, game):
        super().update(game)
        self.x = WIDTH // 2 + math.sin(self.t * 0.015) * (90 + self.index * 8)
        self.y = HEIGHT // 3 + math.cos(self.t * 0.01) * (40 + self.index * 5)
        self.phase_timer += 1
        if self.phase_timer < 200:
            if self.t % 80 == 0:
                for i in range(2 + self.index // 3):
                    rx = self.x + random.uniform(-60, 60); ry = self.y + random.uniform(-60, 60)
                    game.enemies.append(GeometricEnemy(rx, ry, random.choice(['triangle', 'square', 'pentagon']), random.randint(12, 20)))
        elif self.phase_timer < 400:
            if self.t % max(6, 12 - self.index) == 0:
                petals = 5 + (self.index % 4)
                for p in range(petals):
                    base = (self.t * 8 + p * (360 / petals)) % 360
                    for step in range(0, 360, 30):
                        game.boss_bullets.append(Bullet(self.x, self.y, base + step, 5 + (step / 90), owner='boss', damage=1.0))
        else:
            if self.t % max(40, 90 - self.index * 4) == 0:
                angle_to_player = math.degrees(math.atan2(game.player.y - self.y, game.player.x - self.x))
                for k in range(-2, 3):
                    game.boss_bullets.append(Bullet(self.x, self.y, angle_to_player + k * 6, 13 + self.index * 0.4, owner='boss', damage=2.2))
            if self.phase_timer > 600:
                self.phase_timer = 0

BOSS_LIST = [HexagonSentinel, VortexEye, SpiralCore, ShardKing, StarForge]
def spawn_boss_for_wave(boss_index):
    cls = BOSS_LIST[(boss_index - 1) % len(BOSS_LIST)]
    return cls(boss_index)

# ---------------- Shop UI ----------------
class Shop:
    def __init__(self, game):
        self.game = game
        self.open = False
        self.cards = []  # clickable rects
        # build ship list sorted by tier
        self.ship_items = sorted(SHIP_DEFS.items(), key=lambda kv: kv[1]['tier'])
        # card sizes
        self.card_w = 240; self.card_h = 120

    def toggle(self):
        self.open = not self.open

    def buy_ship(self, key):
        cost = SHIP_DEFS[key]['cost']
        if self.game.coins >= cost:
            self.game.coins -= cost
            # equip new ship while preserving position, velocity, lives
            oldx, oldy = self.game.player.x, self.game.player.y
            oldvx, oldvy = self.game.player.vx, self.game.player.vy
            old_lives = self.game.player.lives
            self.game.player = Player(key)
            self.game.player.x, self.game.player.y = oldx, oldy
            self.game.player.vx, self.game.player.vy = oldvx, oldvy
            self.game.player.lives = old_lives
            self.game.owned_ships.add(key)
            self.game.floaters.append(FloatingText(f"Bought: {key}", YELLOW, x=oldx, y=oldy))
            return True
        else:
            self.game.floaters.append(FloatingText("Not enough coins", RED, x=self.game.player.x, y=self.game.player.y))
            return False

    def draw(self, surf):
        # semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 4, 6, 220))
        surf.blit(overlay, (0, 0))
        # title
        title = neon_text("SHOP", FONT_XL, MAGENTA, glow_color=PURPLE)
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 24))
        coins_t = FONT_MED.render(f"Coins: {self.game.coins}", True, YELLOW)
        surf.blit(coins_t, (WIDTH // 2 - coins_t.get_width() // 2, 90))
        # grid of cards
        self.cards.clear()
        gap = 18
        cols = 3
        rows = (len(self.ship_items) + cols - 1) // cols
        start_x = WIDTH // 2 - (cols * self.card_w + (cols - 1) * gap) // 2
        start_y = 140
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(self.ship_items):
                    break
                name, info = self.ship_items[idx]
                rx = start_x + c * (self.card_w + gap)
                ry = start_y + r * (self.card_h + gap)
                rect = pygame.Rect(rx, ry, self.card_w, self.card_h)
                # border color depends
                if name in self.game.owned_ships:
                    border = CYAN
                elif self.game.coins >= info['cost']:
                    border = LIME
                else:
                    border = GRAY
                pygame.draw.rect(surf, (14, 14, 18), rect)
                pygame.draw.rect(surf, border, rect, 3)
                # content
                nm = FONT_MED.render(name, True, WHITE)
                surf.blit(nm, (rx + 10, ry + 8))
                desc = FONT_SMALL.render(info['desc'], True, (200, 200, 200))
                surf.blit(desc, (rx + 10, ry + 36))
                cost_txt = FONT_MED.render(f"Cost: {info['cost']}", True, YELLOW)
                surf.blit(cost_txt, (rx + 10, ry + 66))
                stat_line = f"SPD:{info['speed']} DMG:{info['bullet_dmg']} CD:{info['shoot_delay']}"
                stat = FONT_SMALL.render(stat_line, True, (180, 180, 200))
                surf.blit(stat, (rx + 10, ry + 92))
                # owned/equip indicator
                if name in self.game.owned_ships:
                    tag = FONT_SMALL.render("OWNED - Click to Equip", True, CYAN)
                    surf.blit(tag, (rx + 130, ry + 10))
                self.cards.append((rect, name))
                idx += 1
        footer = FONT_SMALL.render("Click a card to buy/equip for this run. Press P to close shop.", True, WHITE)
        surf.blit(footer, (WIDTH // 2 - footer.get_width() // 2, HEIGHT - 50))

    def click(self, pos):
        for rect, name in self.cards:
            if rect.collidepoint(pos):
                if name in self.game.owned_ships:
                    # Equip
                    oldx, oldy = self.game.player.x, self.game.player.y
                    oldvx, oldvy = self.game.player.vx, self.game.player.vy
                    old_lives = self.game.player.lives
                    self.game.player = Player(name)
                    self.game.player.x, self.game.player.y = oldx, oldy
                    self.game.player.vx, self.game.player.vy = oldvx, oldvy
                    self.game.player.lives = old_lives
                    self.game.floaters.append(FloatingText(f"Equipped: {name}", CYAN, x=oldx, y=oldy))
                else:
                    self.buy_ship(name)
                break

# ---------------- Floating text for notifications ----------------
class FloatingText:
    def __init__(self, text, color, life=90, x=None, y=None):
        self.text = text
        self.color = color
        self.life = life
        self.max = life
        self.x = x if x is not None else WIDTH // 2
        self.y = y if y is not None else HEIGHT // 2

    def update(self):
        self.y -= 0.36
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0: return
        alpha = clamp(int(255 * (self.life / self.max)), 0, 255)
        surf_t = FONT_MED.render(self.text, True, self.color)
        tmp = pygame.Surface(surf_t.get_size(), pygame.SRCALPHA)
        tmp.blit(surf_t, (0, 0))
        tmp.set_alpha(alpha)
        surf.blit(tmp, (self.x - surf_t.get_width() // 2, self.y))

# ---------------- Game class (core) ----------------
class Game:
    def __init__(self):
        self.player = Player("Scout")  # default ship
        self.bullets = []
        self.enemies = []
        self.boss = None
        self.boss_bullets = []
        self.particles = []
        self.powerups = []
        self.wave = 1
        self.score = 0
        self.coins = 0
        self.total_coins = 0
        self.wave_complete = False
        self.wave_timer = 0
        self.floaters = deque()
        self.shop = Shop(self)
        self.owned_ships = set(["Scout"])
        self.game_over = False
        self.difficulty = 1.0
        self.spawn_wave()

    def spawn_wave(self):
        self.wave_complete = False
        self.wave_timer = 0
        # every 4th wave is boss (3 normals then boss)
        if self.wave % 4 == 0:
            boss_index = self.wave // 4
            self.boss = spawn_boss_for_wave(boss_index)
            self.boss.start()
            self.boss.x = WIDTH // 2
            self.boss.y = -140
            self.floaters.append(FloatingText(f"BOSS WAVE {boss_index}", MAGENTA, life=120))
        else:
            # normal wave spawn
            types = ['triangle', 'square', 'pentagon', 'hexagon']
            count = max(3, 3 + int(self.wave * 1.6))
            for _ in range(count):
                side = random.randint(0, 3)
                if side == 0: x = random.randint(0, WIDTH); y = -60
                elif side == 1: x = WIDTH + 60; y = random.randint(0, HEIGHT)
                elif side == 2: x = random.randint(0, WIDTH); y = HEIGHT + 60
                else: x = -60; y = random.randint(0, HEIGHT)
                t = random.choice(types[:min(len(types), 1 + self.wave // 3)])
                size = random.randint(18, 34)
                self.enemies.append(GeometricEnemy(x, y, t, size, scale=1.0 + self.difficulty * 0.04))
            self.floaters.append(FloatingText(f"WAVE {self.wave}", CYAN, life=80))

    def add_coins(self, amt, x=None, y=None):
        self.coins += amt
        self.total_coins += amt
        fx = x if x is not None else self.player.x
        fy = y if y is not None else self.player.y
        self.floaters.append(FloatingText(f"+{amt} coins", YELLOW, life=70, x=fx, y=fy))

    def handle_input(self):
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        mbtns = pygame.mouse.get_pressed()
        if self.shop.open:
            return
        # mouse aiming
        dx = mx - self.player.x; dy = my - self.player.y
        targ = math.degrees(math.atan2(dy, dx))
        diff = (targ - getattr(self.player, "angle", 0) + 180) % 360 - 180
        if abs(diff) > 2:
            self.player.rotate(1 if diff > 0 else -1)
        if keys[pygame.K_LEFT]: self.player.rotate(-1)
        if keys[pygame.K_RIGHT]: self.player.rotate(1)
        if keys[pygame.K_UP] or keys[pygame.K_w] or mbtns[2]: self.player.thrust()
        # shooting
        if (mbtns[0] or keys[pygame.K_SPACE]) and self.player.can_shoot():
            self.player.shoot()
            sdef = SHIP_DEFS[self.player.ship_name]
            # ship-specific firing
            if self.player.ship_name == "Blazer":
                for off in (-6, 0, 6):
                    self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle + off, sdef['bullet_speed'], owner='player', damage=sdef['bullet_dmg']))
            elif self.player.ship_name == "Destroyer":
                for off in (-8, 8):
                    self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle + off, sdef['bullet_speed'] - 1, owner='player', damage=sdef['bullet_dmg']))
            elif self.player.ship_name == "Nova":
                b = Bullet(self.player.x, self.player.y, self.player.angle, sdef['bullet_speed'], owner='player', damage=sdef['bullet_dmg'])
                b.radius = 5
                self.bullets.append(b)
            elif self.player.ship_name == "Vector":
                # two fast bullets
                for off in (-2, 2):
                    self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle + off, sdef['bullet_speed'], owner='player', damage=sdef['bullet_dmg']))
            else:
                # Scout & Fighter default
                self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle, sdef['bullet_speed'], owner='player', damage=sdef['bullet_dmg']))

    def update(self):
        # update floaters
        for _ in range(len(self.floaters)):
            try:
                f = self.floaters[0]
                f.update()
                if f.life <= 0:
                    self.floaters.popleft()
                else:
                    # rotate queue to allow in-place update
                    self.floaters.rotate(-1)
            except IndexError:
                break

        # pause updates if shop open or game over
        if self.shop.open or self.game_over:
            return

        # update player & bullets & enemies & boss & powerups & particles
        self.player.update()
        for b in self.bullets[:]:
            b.update(self.enemies)
            if not b.is_alive():
                try: self.bullets.remove(b)
                except: pass
        for bb in self.boss_bullets[:]:
            bb.update(self.enemies)
            if not bb.is_alive():
                try: self.boss_bullets.remove(bb)
                except: pass
        for e in self.enemies[:]:
            e.update(self.player.x, self.player.y, diff=self.difficulty)
        if self.boss:
            self.boss.update(self)
        for pu in self.powerups[:]:
            pu.update()
            if not pu.is_alive():
                try: self.powerups.remove(pu)
                except: pass
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                try: self.particles.remove(p)
                except: pass

        # collisions: bullets -> boss (boss priority)
        if self.boss:
            for b in self.bullets[:]:
                if distance(b.x, b.y, self.boss.x, self.boss.y) < (self.boss.size):
                    try: self.bullets.remove(b)
                    except: pass
                    if self.boss.hit(b.damage):
                        # boss defeated
                        reward = 220 + self.boss.index * 80
                        self.add_coins(reward, self.boss.x, self.boss.y)
                        self.score += 1000 + self.boss.index * 200
                        for _ in range(60):
                            self.particles.append(Particle(self.boss.x + random.uniform(-40, 40), self.boss.y + random.uniform(-40, 40), self.boss.color))
                        if random.random() < 1.0:
                            self.powerups.append(PowerUp(self.boss.x, self.boss.y, random.choice(['spread', 'rapid', 'life', 'shield'])))
                        self.boss_bullets.clear()
                        self.boss = None
                        self.wave_complete = True
                        self.wave += 1
                        self.wave_timer = 200
                        self.difficulty += 0.06
                        break

        # collisions: bullets -> enemies
        for b in self.bullets[:]:
            hit_flag = False
            for e in self.enemies[:]:
                if distance(b.x, b.y, e.x, e.y) < e.size:
                    try: self.bullets.remove(b)
                    except: pass
                    if e.hit(b.damage):
                        self.score += e.sides * 10
                        coins = int(e.coin)
                        self.add_coins(coins, e.x, e.y)
                        for _ in range(10):
                            self.particles.append(Particle(e.x + random.uniform(-6, 6), e.y + random.uniform(-6, 6), e.color))
                        new = e.split()
                        try: self.enemies.remove(e)
                        except: pass
                        self.enemies.extend(new)
                        if random.random() < 0.10:
                            self.powerups.append(PowerUp(e.x, e.y, random.choice(['spread', 'rapid', 'life', 'shield'])))
                    hit_flag = True
                    break
            if hit_flag: continue

        # boss bullets hitting player
        for bb in self.boss_bullets[:]:
            if distance(bb.x, bb.y, self.player.x, self.player.y) < bb.radius + self.player.radius:
                try: self.boss_bullets.remove(bb)
                except: pass
                if self.player.invulnerable == 0:
                    self.player.lives -= 1
                    self.player.invulnerable = 90
                    for _ in range(18):
                        self.particles.append(Particle(self.player.x + random.uniform(-6, 6), self.player.y + random.uniform(-6, 6), CYAN))
                    if self.player.lives <= 0:
                        self.game_over = True
                break

        # player collides with enemies
        if self.player.invulnerable == 0:
            for e in self.enemies[:]:
                if distance(e.x, e.y, self.player.x, self.player.y) < e.size + self.player.radius:
                    self.player.lives -= 1
                    self.player.invulnerable = 120
                    for _ in range(20):
                        self.particles.append(Particle(self.player.x + random.uniform(-6, 6), self.player.y + random.uniform(-6, 6), CYAN))
                    if self.player.lives <= 0:
                        self.game_over = True
                    try: self.enemies.remove(e)
                    except: pass
                    break

        # picking up powerups
        for pu in self.powerups[:]:
            if distance(pu.x, pu.y, self.player.x, self.player.y) < pu.radius + self.player.radius:
                try: self.powerups.remove(pu)
                except: pass
                if pu.type == 'life':
                    self.player.lives += 1
                    self.score += 100
                elif pu.type == 'spread':
                    self.player.weapon_type = 'spread'
                    self.player.weapon_timer = 300
                elif pu.type == 'rapid':
                    self.player.weapon_type = 'rapid'
                    self.player.weapon_timer = 300
                elif pu.type == 'shield':
                    self.player.invulnerable = 180
                for _ in range(14):
                    self.particles.append(Particle(pu.x + random.uniform(-6, 6), pu.y + random.uniform(-6, 6), LIME))

        # check wave completion for normal waves
        if self.boss is None and not self.enemies and not self.wave_complete:
            self.wave_complete = True
            self.wave_timer = 120
            self.wave += 1
            self.score += int(50 * (1 + self.difficulty * 0.1))
            self.add_coins(25, self.player.x, self.player.y)
            self.difficulty += 0.02

        if self.wave_complete:
            self.wave_timer -= 1
            if self.wave_timer <= 0:
                self.spawn_wave()

    def draw_grid(self):
        for x in range(0, WIDTH, 50):
            pygame.draw.line(screen, DARK_GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(screen, DARK_GRID, (0, y), (WIDTH, y), 1)

    def draw_ui(self):
        ui = pygame.Surface((240, 160), pygame.SRCALPHA)
        ui.fill((0, 0, 0, 150))
        screen.blit(ui, (8, 8))
        score_t = FONT_MED.render(f"Score: {self.score}", True, WHITE)
        wave_t = FONT_MED.render(f"Wave: {self.wave}", True, CYAN)
        lives_t = FONT_MED.render(f"Lives: {self.player.lives}", True, GREEN)
        coins_t = FONT_MED.render(f"Coins: {self.coins}", True, YELLOW)
        ship_t = FONT_SMALL.render(f"Ship: {self.player.ship_name}", True, self.player.color)
        screen.blit(score_t, (16, 12))
        screen.blit(wave_t, (16, 42))
        screen.blit(lives_t, (16, 72))
        screen.blit(coins_t, (16, 102))
        screen.blit(ship_t, (16, 132))
        hint = FONT_SMALL.render("Press P to open Shop (pauses).", True, GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 28))

    def draw(self):
        # background & grid
        screen.fill(BLACK)
        self.draw_grid()
        # particles (behind)
        for p in self.particles: p.draw(screen)
        # boss behind bullets for glow layering
        if self.boss: self.boss.draw(screen)
        # enemies
        for e in self.enemies: e.draw(screen)
        # powerups
        for pu in self.powerups: pu.draw(screen)
        # bullets
        for b in self.bullets: b.draw(screen)
        for bb in self.boss_bullets: bb.draw(screen)
        # player
        self.player.draw(screen)
        # floating texts
        for f in self.floaters: f.draw(screen)
        # ui
        self.draw_ui()
        # shop overlay if open
        if self.shop.open:
            self.shop.draw(screen)
        # game over overlay
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            go = neon_text("GAME OVER", FONT_XL, RED, glow_color=PURPLE)
            screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 120))
            sc = FONT_LARGE.render(f"Final Score: {self.score}", True, WHITE)
            screen.blit(sc, (WIDTH // 2 - sc.get_width() // 2, HEIGHT // 2 - 40))
            inst = FONT_MED.render("Press SPACE to restart", True, WHITE)
            screen.blit(inst, (WIDTH // 2 - inst.get_width() // 2, HEIGHT // 2 + 40))

    def click(self, pos):
        if self.shop.open:
            self.shop.click(pos)

# ---------------- Main loop ----------------
def main():
    game = Game()
    running = True

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE and game.game_over:
                    game = Game()  # reset full run
                if event.key == pygame.K_p:
                    # toggle shop
                    # note: P key was requested
                    game.shop.toggle()
                if event.key == pygame.K_RETURN and game.shop.open:
                    game.shop.toggle()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game.shop.open:
                        game.shop.click(event.pos)
                    else:
                        # immediate click handled by handle_input (shoot)
                        pass

        # Input & update
        game.handle_input()
        game.update()
        # Draw
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
