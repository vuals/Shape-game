import pygame
import random
import math
import sys

pygame.init()

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

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 0
        self.vel_x = 0
        self.vel_y = 0
        self.acceleration = 0.3
        self.friction = 0.98
        self.max_speed = 8
        self.damage = 1
        self.radius = 12
        self.shoot_cooldown = 0
        self.default_shoot_delay = 10
        self.shoot_delay = self.default_shoot_delay
        self.lives = 3
        self.invulnerable = 0
        self.weapon_type = 'normal'
        self.weapon_timer = 0
        
    def rotate(self, direction):
        self.angle += direction * 5
    
    def thrust(self):
        rad = math.radians(self.angle)
        self.vel_x += math.cos(rad) * self.acceleration
        self.vel_y += math.sin(rad) * self.acceleration
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        if speed > self.max_speed:
            self.vel_x = (self.vel_x / speed) * self.max_speed
            self.vel_y = (self.vel_y / speed) * self.max_speed
    
    def update(self):
        self.vel_x *= self.friction
        self.vel_y *= self.friction
        self.x += self.vel_x
        self.y += self.vel_y
        
        if self.x < 0: self.x = WIDTH
        elif self.x > WIDTH: self.x = 0
        if self.y < 0: self.y = HEIGHT
        elif self.y > HEIGHT: self.y = 0
        
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.invulnerable > 0: self.invulnerable -= 1
        if self.weapon_timer > 0:
            self.weapon_timer -= 1
        else:
            if self.weapon_type != 'normal':
                self.weapon_type = 'normal'
                self.shoot_delay = self.default_shoot_delay
    
    def can_shoot(self):
        return self.shoot_cooldown == 0
    
    def shoot(self):
        self.shoot_cooldown = self.shoot_delay
    
    def draw(self, screen):
        if self.invulnerable > 0 and self.invulnerable % 10 < 5:
            return
        
        rad = math.radians(self.angle)
        front_x = self.x + math.cos(rad) * self.radius
        front_y = self.y + math.sin(rad) * self.radius
        back_left_x = self.x + math.cos(rad + 2.5) * self.radius
        back_left_y = self.y + math.sin(rad + 2.5) * self.radius
        back_right_x = self.x + math.cos(rad - 2.5) * self.radius
        back_right_y = self.y + math.sin(rad - 2.5) * self.radius
        
        color = CYAN
        if self.weapon_type == 'spread': color = YELLOW
        elif self.weapon_type == 'rapid': color = MAGENTA
        
        pygame.draw.polygon(screen, color, [(front_x, front_y), (back_left_x, back_left_y), 
                                            (self.x, self.y), (back_right_x, back_right_y)], 2)
        
        if abs(self.vel_x) > 0.5 or abs(self.vel_y) > 0.5:
            back_x = self.x - math.cos(rad) * self.radius * 0.8
            back_y = self.y - math.sin(rad) * self.radius * 0.8
            pygame.draw.circle(screen, ORANGE, (int(back_x), int(back_y)), 3)

class Bullet:
    def __init__(self, x, y, angle, speed=10, owner='player', damage=1):
        self.x, self.y = x, y
        rad = math.radians(angle)
        self.vel_x = math.cos(rad) * speed
        self.vel_y = math.sin(rad) * speed
        self.lifetime = 60
        self.radius = 3
        self.owner = owner
        self.color = WHITE if owner == 'player' else RED
        self.damage = damage
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifetime -= 1
        if self.x < 0: self.x = WIDTH
        elif self.x > WIDTH: self.x = 0
        if self.y < 0: self.y = HEIGHT
        elif self.y > HEIGHT: self.y = 0
    
    def is_alive(self):
        return self.lifetime > 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class GeometricEnemy:
    def __init__(self, x, y, shape_type, size):
        self.x, self.y = x, y
        self.shape_type = shape_type
        self.size = size
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        
        configs = {
            'triangle': (3, RED, 2.5, 1, 5),
            'square': (4, ORANGE, 1.5, 2, 10),
            'pentagon': (5, YELLOW, 1, 3, 20),
            'hexagon': (6, GREEN, 0.8, 4, 35)
        }
        self.sides, self.color, self.speed, self.health, self.coin_value = configs[shape_type]
        
        angle_rad = random.uniform(0, 2 * math.pi)
        self.vel_x = math.cos(angle_rad) * self.speed
        self.vel_y = math.sin(angle_rad) * self.speed
        
    def update(self, player_x, player_y):
        dx, dy = player_x - self.x, player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.vel_x += (dx / dist) * 0.05
            self.vel_y += (dy / dist) * 0.05
        
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        if speed > self.speed:
            self.vel_x = (self.vel_x / speed) * self.speed
            self.vel_y = (self.vel_y / speed) * self.speed
        
        self.x += self.vel_x
        self.y += self.vel_y
        self.angle += self.rotation_speed
        
        if self.x < -50: self.x = WIDTH + 50
        elif self.x > WIDTH + 50: self.x = -50
        if self.y < -50: self.y = HEIGHT + 50
        elif self.y > HEIGHT + 50: self.y = -50
    
    def hit(self, damage=1):
        self.health -= damage
        return self.health <= 0
    
    def split(self):
        if self.size > 15:
            new_shapes = []
            for i in range(2):
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                new_shape = GeometricEnemy(self.x + math.cos(rad) * 20, self.y + math.sin(rad) * 20,
                                          self.shape_type, max(10, self.size // 2))
                new_shapes.append(new_shape)
            return new_shapes
        return []
    
    def draw(self, screen):
        points = [(self.x + math.cos(math.radians(self.angle + (360 / self.sides) * i)) * self.size,
                   self.y + math.sin(math.radians(self.angle + (360 / self.sides) * i)) * self.size)
                  for i in range(self.sides)]
        pygame.draw.polygon(screen, self.color, points, 3)
        
        inner_points = [(self.x + math.cos(math.radians(self.angle + (360 / self.sides) * i)) * (self.size * 0.7),
                        self.y + math.sin(math.radians(self.angle + (360 / self.sides) * i)) * (self.size * 0.7))
                       for i in range(self.sides)]
        pygame.draw.polygon(screen, self.color, inner_points, 1)

class BossEnemy:
    def __init__(self, x, y, boss_index):
        self.x, self.y = x, y
        self.angle = random.uniform(0, 360)
        self.size = 70 + (boss_index * 10)
        self.color = PURPLE if boss_index % 2 == 0 else BLUE
        self.health = 80 + (boss_index * 35)
        self.max_health = self.health
        self.speed = 0.5 + (boss_index * 0.12)
        self.rotation_speed = random.uniform(-1, 1)
        self.minion_timer = 160
        self.attack_timer = 90
        self.boss_index = boss_index
        self.sides = 8
        self.type = (boss_index - 1) % 3
        self.minion_strength = max(1, 1 + boss_index // 3)
        self.projectile_speed = 6 + boss_index
        self.projectile_count = 1 + (boss_index // 2)
    
    def update(self, player_x, player_y, enemies, boss_projectiles):
        dx, dy = player_x - self.x, player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        self.angle += self.rotation_speed

        if self.x < -120: self.x = WIDTH + 120
        elif self.x > WIDTH + 120: self.x = -120
        if self.y < -120: self.y = HEIGHT + 120
        elif self.y > HEIGHT + 120: self.y = -120

        angle_to_player = math.degrees(math.atan2(player_y - self.y, player_x - self.x))

        if self.type == 0:
            self.minion_timer -= 1
            if self.minion_timer <= 0:
                self.minion_timer = max(50, 160 - (self.boss_index * 8))
                for _ in range(random.randint(1, min(2, self.minion_strength))):
                    enemies.append(GeometricEnemy(self.x + random.uniform(-30, 30), 
                                                  self.y + random.uniform(-30, 30),
                                                  random.choice(['triangle', 'square']), 20))
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_timer = 200 - (self.boss_index * 4)
                boss_projectiles.append(Bullet(self.x, self.y, angle_to_player + random.uniform(-8, 8),
                                              speed=self.projectile_speed - 2, owner='boss'))

        elif self.type == 1:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_timer = max(30, 110 - (self.boss_index * 6))
                spread = 10 + (self.boss_index * 1.5)
                for i in range(self.projectile_count):
                    offset = (i - (self.projectile_count - 1) / 2) * (spread / max(1, self.projectile_count))
                    boss_projectiles.append(Bullet(self.x, self.y, angle_to_player + offset, 
                                                   speed=self.projectile_speed, owner='boss'))
            self.minion_timer -= 1
            if self.minion_timer <= 0:
                self.minion_timer = 240
                if random.random() < 0.4:
                    enemies.append(GeometricEnemy(self.x + random.uniform(-20, 20),
                                                  self.y + random.uniform(-20, 20),
                                                  random.choice(['triangle', 'square']), 22))
        else:
            self.minion_timer -= 1
            self.attack_timer -= 1
            if self.minion_timer <= 0:
                self.minion_timer = max(80, 180 - (self.boss_index * 6))
                if random.random() < 0.8:
                    enemies.append(GeometricEnemy(self.x + random.uniform(-25, 25),
                                                  self.y + random.uniform(-25, 25),
                                                  random.choice(['triangle', 'square']), 22))
            if self.attack_timer <= 0:
                self.attack_timer = max(60, 150 - (self.boss_index * 5))
                for i in range(random.randint(1, self.projectile_count)):
                    boss_projectiles.append(Bullet(self.x, self.y, angle_to_player + random.uniform(-12, 12),
                                                   speed=self.projectile_speed, owner='boss'))

    def hit(self, damage=1):
        self.health -= damage
        return self.health <= 0

    def draw(self, screen):
        points = [(self.x + math.cos(math.radians(self.angle + (360 / self.sides) * i)) * self.size,
                   self.y + math.sin(math.radians(self.angle + (360 / self.sides) * i)) * self.size)
                  for i in range(self.sides)]
        pygame.draw.polygon(screen, self.color, points, 4)

        health_ratio = max(0, self.health / self.max_health)
        bar_width, bar_height = 160, 12
        pygame.draw.rect(screen, RED, (self.x - bar_width/2, self.y - self.size - 30, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (self.x - bar_width/2, self.y - self.size - 30, 
                                        bar_width * health_ratio, bar_height))

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x, self.y = x, y
        self.type = power_type
        self.lifetime = 300
        self.radius = 15
        colors = {'spread': YELLOW, 'rapid': MAGENTA, 'life': GREEN}
        self.color = colors[power_type]
    
    def update(self):
        self.lifetime -= 1
    
    def is_alive(self):
        return self.lifetime > 0
    
    def draw(self, screen):
        pulse = abs((self.lifetime % 40) - 20) / 20
        radius = int(self.radius + pulse * 5)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), radius, 2)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), radius - 5, 1)

class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.x, self.y = x, y
        self.vel_x = math.cos(angle) * speed
        self.vel_y = math.sin(angle) * speed
        self.color = color
        self.lifetime = 30
        self.size = random.randint(2, 4)
    
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifetime -= 1
        self.vel_x *= 0.95
        self.vel_y *= 0.95
    
    def is_alive(self):
        return self.lifetime > 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class GeometricAsteroids:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Geometric Asteroids")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.prev_s = False
        self.reset_game()
    
    def reset_game(self):
        self.player = Player()
        self.bullets, self.enemies, self.powerups, self.particles, self.boss_projectiles = [], [], [], [], []
        self.boss = None
        self.score, self.coins, self.wave = 0, 0, 1
        self.game_over, self.wave_complete, self.shop_open = False, False, False
        self.wave_timer = 0
        self.owned_upgrades = {}
        self.shop_items = [
            {'id': 'speed', 'name': 'Increase Speed', 'cost': 150, 'desc': '+1 max speed'},
            {'id': 'damage', 'name': 'Increase Damage', 'cost': 200, 'desc': '+1 bullet damage'},
            {'id': 'firerate', 'name': 'Faster Fire', 'cost': 180, 'desc': '-1 shoot delay'},
            {'id': 'life', 'name': 'Extra Life', 'cost': 250, 'desc': '+1 life'}
        ]
        self.shop_rects = []
        self.spawn_wave()
    
    def spawn_wave(self):
        self.wave_complete = False
        self.boss = None
        self.boss_projectiles = []
        
        if self.wave % 4 == 0:
            self.boss = BossEnemy(WIDTH // 2, -150, self.wave // 4)
            return
        
        shape_types = ['triangle', 'square', 'pentagon', 'hexagon']
        for _ in range(3 + self.wave * 2):
            side = random.randint(0, 3)
            positions = [(random.randint(0, WIDTH), -50), (WIDTH + 50, random.randint(0, HEIGHT)),
                        (random.randint(0, WIDTH), HEIGHT + 50), (-50, random.randint(0, HEIGHT))]
            x, y = positions[side]
            shape_type = random.choice(shape_types[:min(len(shape_types), 1 + self.wave // 2)])
            self.enemies.append(GeometricEnemy(x, y, shape_type, random.randint(20, 40)))
    
    def handle_input(self):
        if self.shop_open: return
        keys, mouse_pos, mouse_buttons = pygame.key.get_pressed(), pygame.mouse.get_pos(), pygame.mouse.get_pressed()
        
        dx, dy = mouse_pos[0] - self.player.x, mouse_pos[1] - self.player.y
        target_angle = math.degrees(math.atan2(dy, dx))
        angle_diff = target_angle - self.player.angle
        while angle_diff > 180: angle_diff -= 360
        while angle_diff < -180: angle_diff += 360
        
        if abs(angle_diff) > 2:
            self.player.rotate(1 if angle_diff > 0 else -1)
        
        if keys[pygame.K_LEFT]: self.player.rotate(-1)
        if keys[pygame.K_RIGHT]: self.player.rotate(1)
        if keys[pygame.K_UP] or keys[pygame.K_w] or mouse_buttons[2]: self.player.thrust()
        if mouse_buttons[0] or keys[pygame.K_SPACE]:
            if self.player.can_shoot(): self.shoot()
    
    def shoot(self):
        delays = {'spread': 10, 'rapid': 3, 'normal': self.player.default_shoot_delay}
        self.player.shoot_delay = delays.get(self.player.weapon_type, self.player.default_shoot_delay)
        self.player.shoot()
        
        if self.player.weapon_type == 'spread':
            for offset in [-15, 0, 15]:
                self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle + offset, 
                                          10, 'player', self.player.damage))
        else:
            speed = 15 if self.player.weapon_type == 'rapid' else 10
            self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle, 
                                      speed, 'player', self.player.damage))
    
    def update(self):
        if self.shop_open: return
        self.player.update()
        
        for lst in [self.bullets, self.boss_projectiles, self.powerups, self.particles]:
            for item in lst[:]:
                item.update()
                if not item.is_alive():
                    try: lst.remove(item)
                    except ValueError: pass
        
        for enemy in self.enemies:
            enemy.update(self.player.x, self.player.y)
        
        if self.boss:
            self.boss.update(self.player.x, self.player.y, self.enemies, self.boss_projectiles)
        
        # Boss collision
        if self.boss:
            for bullet in self.bullets[:]:
                if math.sqrt((bullet.x - self.boss.x)**2 + (bullet.y - self.boss.y)**2) < self.boss.size:
                    try: self.bullets.remove(bullet)
                    except ValueError: pass
                    if self.boss.hit(bullet.damage):
                        self.score += 1200 + (self.boss.boss_index * 800)
                        self.coins += 200 + (self.boss.boss_index * 60)
                        self.wave += 1
                        self.wave_complete, self.wave_timer = True, 200
                        for _ in range(60):
                            self.particles.append(Particle(self.boss.x + random.uniform(-30,30),
                                                          self.boss.y + random.uniform(-30,30), PURPLE))
                        self.powerups.append(PowerUp(self.boss.x, self.boss.y, random.choice(['spread', 'rapid', 'life'])))
                        self.boss = None
                        self.boss_projectiles = []
                        break
        
        # Enemy collision
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2) < enemy.size:
                    try: self.bullets.remove(bullet)
                    except ValueError: pass
                    if enemy.hit(bullet.damage):
                        self.score += enemy.sides * 10
                        self.coins += enemy.coin_value
                        for _ in range(8):
                            self.particles.append(Particle(enemy.x, enemy.y, enemy.color))
                        try: self.enemies.remove(enemy)
                        except ValueError: pass
                        self.enemies.extend(enemy.split())
                        if random.random() < 0.1:
                            self.powerups.append(PowerUp(enemy.x, enemy.y, random.choice(['spread', 'rapid', 'life'])))
                    break
        
        # Boss projectile collision
        for bproj in self.boss_projectiles[:]:
            if math.sqrt((self.player.x - bproj.x)**2 + (self.player.y - bproj.y)**2) < self.player.radius + bproj.radius:
                try: self.boss_projectiles.remove(bproj)
                except ValueError: pass
                if self.player.invulnerable == 0:
                    self.player.lives -= 1
                    self.player.invulnerable = 100
                    for _ in range(18):
                        self.particles.append(Particle(self.player.x, self.player.y, CYAN))
                    if self.player.lives <= 0: self.game_over = True
                break
        
        # Player-enemy collision
        if self.player.invulnerable == 0:
            for enemy in self.enemies:
                if math.sqrt((self.player.x - enemy.x)**2 + (self.player.y - enemy.y)**2) < enemy.size + self.player.radius:
                    self.player.lives -= 1
                    self.player.invulnerable = 120
                    for _ in range(20):
                        self.particles.append(Particle(self.player.x, self.player.y, CYAN))
                    if self.player.lives <= 0: self.game_over = True
                    break
        
        # Powerup collision
        for powerup in self.powerups[:]:
            if math.sqrt((self.player.x - powerup.x)**2 + (self.player.y - powerup.y)**2) < powerup.radius + self.player.radius:
                try: self.powerups.remove(powerup)
                except ValueError: pass
                if powerup.type == 'life':
                    self.player.lives += 1
                    self.score += 100
                else:
                    self.player.weapon_type = powerup.type
                    self.player.weapon_timer = 300
                for _ in range(15):
                    self.particles.append(Particle(powerup.x, powerup.y, powerup.color))
        
        # Wave completion
        if not self.boss and not self.enemies and not self.boss_projectiles and not self.wave_complete:
            self.wave_complete, self.wave_timer = True, 120
            self.wave += 1
            self.score += self.wave * 100
        
        if self.wave_complete:
            self.wave_timer -= 1
            if self.wave_timer <= 0: self.spawn_wave()
    
    def draw(self):
        self.screen.fill(BLACK)
        for x in range(0, WIDTH, 50):
            pygame.draw.line(self.screen, (20, 20, 40), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(self.screen, (20, 20, 40), (0, y), (WIDTH, y), 1)
        
        for particle in self.particles: particle.draw(self.screen)
        if self.boss: self.boss.draw(self.screen)
        for enemy in self.enemies: enemy.draw(self.screen)
        for powerup in self.powerups: powerup.draw(self.screen)
        for bullet in self.bullets: bullet.draw(self.screen)
        for bproj in self.boss_projectiles: bproj.draw(self.screen)
        self.player.draw(self.screen)
        
        # UI
        ui_bg = pygame.Surface((220, 170))
        ui_bg.set_alpha(180)
        ui_bg.fill(BLACK)
        self.screen.blit(ui_bg, (5, 5))
        
        texts = [
            (f"Score: {self.score}", WHITE, 10),
            (f"Wave: {self.wave}", CYAN, 35),
            (f"Lives: {self.player.lives}", GREEN, 60),
            (f"Coins: {self.coins}", YELLOW, 85),
            ("Press S: Shop", (200, 200, 0), 110)
        ]
        for text, color, y in texts:
            self.screen.blit(self.small_font.render(text, True, color), (10, y))
        
        if self.player.weapon_timer > 0:
            weapon_bg = pygame.Surface((180, 60))
            weapon_bg.set_alpha(180)
            weapon_bg.fill(BLACK)
            self.screen.blit(weapon_bg, (5, HEIGHT - 90))
            self.screen.blit(self.small_font.render(f"Weapon: {self.player.weapon_type.upper()}", True, YELLOW), (10, HEIGHT - 85))
            self.screen.blit(self.small_font.render(f"Time: {self.player.weapon_timer // 60}s", True, WHITE), (10, HEIGHT - 60))
        
        if self.wave_complete and self.wave_timer > 60:
            complete_text = self.font.render("WAVE COMPLETE!", True, GREEN)
            self.screen.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2, HEIGHT // 2))
        
        if not self.shop_open:
            mouse_pos = pygame.mouse.get_pos()
            pygame.draw.circle(self.screen, WHITE, mouse_pos, 8, 1)
            for line in [((mouse_pos[0] - 12, mouse_pos[1]), (mouse_pos[0] - 4, mouse_pos[1])),
                        ((mouse_pos[0] + 4, mouse_pos[1]), (mouse_pos[0] + 12, mouse_pos[1])),
                        ((mouse_pos[0], mouse_pos[1] - 12), (mouse_pos[0], mouse_pos[1] - 4)),
                        ((mouse_pos[0], mouse_pos[1] + 4), (mouse_pos[0], mouse_pos[1] + 12))]:
                pygame.draw.line(self.screen, WHITE, line[0], line[1], 2)
        
        inst = self.small_font.render("W: Thrust | Mouse: Aim & Shoot | SPACE: Shoot", True, (150, 150, 150))
        self.screen.blit(inst, (WIDTH // 2 - 200, HEIGHT - 25))
        
        if self.shop_open:
            self.draw_shop_overlay()
            
        pygame.display.flip()
    
    def draw_shop_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 6, 8, 200))
        self.screen.blit(overlay, (0, 0))
        
        box_w, box_h = 540, 400
        box_x, box_y = WIDTH // 2 - box_w // 2, HEIGHT // 2 - box_h // 2
        pygame.draw.rect(self.screen, (20, 20, 30), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(self.screen, CYAN, (box_x, box_y, box_w, box_h), 3)
        
        title = self.font.render("SHOP", True, WHITE)
        coins = self.small_font.render(f"Coins: {self.coins}", True, YELLOW)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, box_y + 12))
        self.screen.blit(coins, (WIDTH // 2 - coins.get_width() // 2, box_y + 50))
        
        self.shop_rects.clear()
        gap = 16
        cols = 2
        card_w = (box_w - gap * 3) // 2
        card_h = 100
        
        for idx, item in enumerate(self.shop_items):
            r, c = idx // cols, idx % cols
            rx, ry = box_x + gap + c * (card_w + gap), box_y + 100 + r * (card_h + gap)
            rect = pygame.Rect(rx, ry, card_w, card_h)
            pygame.draw.rect(self.screen, (14, 14, 18), rect)
            pygame.draw.rect(self.screen, GREEN if self.coins >= item['cost'] else WHITE, rect, 2)
            
            self.screen.blit(self.small_font.render(item['name'], True, WHITE), (rx + 8, ry + 8))
            self.screen.blit(self.small_font.render(item['desc'], True, (180, 180, 180)), (rx + 8, ry + 36))
            self.screen.blit(self.small_font.render(f"Cost: {item['cost']}", True, YELLOW), (rx + 8, ry + 64))
            self.shop_rects.append((rect, item))
        
        inst = self.small_font.render("Click item to buy | Press S to close", True, (180, 180, 180))
        self.screen.blit(inst, (WIDTH // 2 - inst.get_width() // 2, box_y + box_h - 28))
    
    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        texts = [
            ("GAME OVER", RED, -70),
            (f"Final Score: {self.score}", WHITE, -10),
            (f"Wave Reached: {self.wave}", CYAN, 30),
            ("Press SPACE to restart", WHITE, 70)
        ]
        for text, color, y_offset in texts:
            rendered = self.font.render(text, True, color) if y_offset in [-70, -10] else self.small_font.render(text, True, color)
            self.screen.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, HEIGHT // 2 + y_offset))
        
        pygame.display.flip()
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.game_over:
                        self.reset_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.shop_open:
                        mx, my = event.pos
                        for rect, item in self.shop_rects:
                            if rect.collidepoint(mx, my) and self.coins >= item['cost']:
                                self.coins -= item['cost']
                                upgrades = {
                                    'speed': lambda: setattr(self.player, 'max_speed', self.player.max_speed + 1),
                                    'damage': lambda: setattr(self.player, 'damage', self.player.damage + 1),
                                    'firerate': lambda: setattr(self.player, 'default_shoot_delay', 
                                                               max(1, self.player.default_shoot_delay - 1)),
                                    'life': lambda: setattr(self.player, 'lives', self.player.lives + 1)
                                }
                                upgrades[item['id']]()
                                self.owned_upgrades[item['id']] = self.owned_upgrades.get(item['id'], 0) + 1
                                break
            
            if not self.game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_s] and not self.prev_s:
                    self.shop_open = not self.shop_open
                self.prev_s = keys[pygame.K_s]
                
                self.handle_input()
                self.update()
                self.draw()
            else:
                self.draw_game_over()
            
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GeometricAsteroids()
    game.run()