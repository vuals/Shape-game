import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 900
HEIGHT = 700
FPS = 60

# Colors
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
        self.radius = 12
        self.shoot_cooldown = 0
        self.default_shoot_delay = 10
        self.shoot_delay = self.default_shoot_delay
        self.lives = 3
        self.invulnerable = 0
        self.weapon_type = 'normal'  # normal, spread, rapid
        self.weapon_timer = 0
        
    def rotate(self, direction):
        self.angle += direction * 5
    
    def thrust(self):
        rad = math.radians(self.angle)
        self.vel_x += math.cos(rad) * self.acceleration
        self.vel_y += math.sin(rad) * self.acceleration
        
        # Limit speed
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        if speed > self.max_speed:
            self.vel_x = (self.vel_x / speed) * self.max_speed
            self.vel_y = (self.vel_y / speed) * self.max_speed
    
    def update(self):
        # Apply friction
        self.vel_x *= self.friction
        self.vel_y *= self.friction
        
        # Move
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Wrap around screen
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0
        
        # Update cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1
        if self.weapon_timer > 0:
            self.weapon_timer -= 1
        else:
            # reset weapon to normal when timer expires
            if self.weapon_type != 'normal':
                self.weapon_type = 'normal'
                self.shoot_delay = self.default_shoot_delay
    
    def can_shoot(self):
        return self.shoot_cooldown == 0
    
    def shoot(self):
        self.shoot_cooldown = self.shoot_delay
    
    def draw(self, screen):
        # Flashing when invulnerable handled by skipping draw intermittently
        if self.invulnerable > 0 and self.invulnerable % 10 < 5:
            return
        
        rad = math.radians(self.angle)
        
        # Ship points
        front_x = self.x + math.cos(rad) * self.radius
        front_y = self.y + math.sin(rad) * self.radius
        
        back_left_x = self.x + math.cos(rad + 2.5) * self.radius
        back_left_y = self.y + math.sin(rad + 2.5) * self.radius
        
        back_right_x = self.x + math.cos(rad - 2.5) * self.radius
        back_right_y = self.y + math.sin(rad - 2.5) * self.radius
        
        # Draw ship
        color = CYAN
        if self.weapon_type == 'spread':
            color = YELLOW
        elif self.weapon_type == 'rapid':
            color = MAGENTA
        
        pygame.draw.polygon(screen, color, [
            (front_x, front_y),
            (back_left_x, back_left_y),
            (self.x, self.y),
            (back_right_x, back_right_y)
        ], 2)
        
        # Draw thruster
        if abs(self.vel_x) > 0.5 or abs(self.vel_y) > 0.5:
            back_x = self.x - math.cos(rad) * self.radius * 0.8
            back_y = self.y - math.sin(rad) * self.radius * 0.8
            pygame.draw.circle(screen, ORANGE, (int(back_x), int(back_y)), 3)

class Bullet:
    def __init__(self, x, y, angle, speed=10, owner='player'):
        self.x = x
        self.y = y
        rad = math.radians(angle)
        self.vel_x = math.cos(rad) * speed
        self.vel_y = math.sin(rad) * speed
        self.lifetime = 60
        self.radius = 3
        self.owner = owner  # 'player' or 'boss'
        self.color = WHITE if owner == 'player' else RED
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifetime -= 1
        
        # Wrap around
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0
    
    def is_alive(self):
        return self.lifetime > 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class GeometricEnemy:
    def __init__(self, x, y, shape_type, size):
        self.x = x
        self.y = y
        self.shape_type = shape_type  # 'triangle', 'square', 'pentagon', 'hexagon'
        self.size = size
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        
        # Set properties based on shape
        if shape_type == 'triangle':
            self.sides = 3
            self.color = RED
            self.speed = 2
            self.health = 1
        elif shape_type == 'square':
            self.sides = 4
            self.color = ORANGE
            self.speed = 1.5
            self.health = 2
        elif shape_type == 'pentagon':
            self.sides = 5
            self.color = YELLOW
            self.speed = 1
            self.health = 3
        elif shape_type == 'hexagon':
            self.sides = 6
            self.color = GREEN
            self.speed = 0.8
            self.health = 4
        
        # Random velocity
        angle_rad = random.uniform(0, 2 * math.pi)
        self.vel_x = math.cos(angle_rad) * self.speed
        self.vel_y = math.sin(angle_rad) * self.speed
        
    def update(self, player_x, player_y):
        # Move towards player slowly (Geometry Wars style)
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.vel_x += (dx / dist) * 0.05
            self.vel_y += (dy / dist) * 0.05
        
        # Limit speed
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        if speed > self.speed:
            self.vel_x = (self.vel_x / speed) * self.speed
            self.vel_y = (self.vel_y / speed) * self.speed
        
        self.x += self.vel_x
        self.y += self.vel_y
        self.angle += self.rotation_speed
        
        # Wrap around
        if self.x < -50:
            self.x = WIDTH + 50
        elif self.x > WIDTH + 50:
            self.x = -50
        if self.y < -50:
            self.y = HEIGHT + 50
        elif self.y > HEIGHT + 50:
            self.y = -50
    
    def hit(self, damage=1):
        self.health -= damage
        return self.health <= 0
    
    def split(self):
        if self.size > 15:
            # Split into smaller shapes
            new_shapes = []
            for i in range(2):
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                offset_x = math.cos(rad) * 20
                offset_y = math.sin(rad) * 20
                new_shape = GeometricEnemy(
                    self.x + offset_x,
                    self.y + offset_y,
                    self.shape_type,
                    max(10, self.size // 2)
                )
                new_shapes.append(new_shape)
            return new_shapes
        return []
    
    def draw(self, screen):
        points = []
        for i in range(self.sides):
            angle_rad = math.radians(self.angle + (360 / self.sides) * i)
            px = self.x + math.cos(angle_rad) * self.size
            py = self.y + math.sin(angle_rad) * self.size
            points.append((px, py))
        
        # Draw with glow effect
        pygame.draw.polygon(screen, self.color, points, 3)
        
        # Inner glow
        inner_points = []
        for i in range(self.sides):
            angle_rad = math.radians(self.angle + (360 / self.sides) * i)
            px = self.x + math.cos(angle_rad) * (self.size * 0.7)
            py = self.y + math.sin(angle_rad) * (self.size * 0.7)
            inner_points.append((px, py))
        pygame.draw.polygon(screen, self.color, inner_points, 1)

class BossEnemy:
    """
    Boss types:
      type 0 -> spawner-focused (spawns few minions; minimal shooting)
      type 1 -> shooter-focused (fires projectiles at player; few or no minions)
      type 2 -> mixed (both spawn & shoot, but at lowered rates)
    """
    def __init__(self, x, y, boss_index):
        # boss_index: 1 for first boss wave (wave 3), 2 for second (wave 6), ...
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 360)
        self.size = 70 + (boss_index * 10)
        self.color = PURPLE if boss_index % 2 == 0 else BLUE
        self.health = 80 + (boss_index * 35)
        self.max_health = self.health
        self.speed = 0.5 + (boss_index * 0.12)
        self.rotation_speed = random.uniform(-1, 1)
        self.minion_timer = 160  # time until next minion spawn
        self.attack_timer = 90   # time until next projectile burst
        self.boss_index = boss_index
        self.sides = 8
        # Determine boss type by index to vary behavior
        self.type = (boss_index - 1) % 3  # 0,1,2 repeating cycle
        # tune spawn/shoot aggressiveness (minions fewer than before)
        self.minion_strength = max(1, 1 + boss_index // 3)  # how many minions at once (small)
        self.projectile_speed = 6 + boss_index  # projectile speed scales
        self.projectile_count = 1 + (boss_index // 2)  # how many projectiles per burst (small)
    
    def update(self, player_x, player_y, enemies, boss_projectiles):
        # Move toward player slowly
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        
        self.angle += self.rotation_speed

        # Wrap around
        if self.x < -120:
            self.x = WIDTH + 120
        elif self.x > WIDTH + 120:
            self.x = -120
        if self.y < -120:
            self.y = HEIGHT + 120
        elif self.y > HEIGHT + 120:
            self.y = -120

        # Behavior branching
        # TYPE 0: spawner-focused (but spawn fewer minions than older design)
        if self.type == 0:
            self.minion_timer -= 1
            spawn_interval = max(50, 160 - (self.boss_index * 8))
            if self.minion_timer <= 0:
                self.minion_timer = spawn_interval
                # spawn 1 or 2 small minions only
                for _ in range(random.randint(1, min(2, self.minion_strength))):
                    enemies.append(
                        GeometricEnemy(self.x + random.uniform(-30, 30),
                                       self.y + random.uniform(-30, 30),
                                       random.choice(['triangle', 'square']),
                                       20)
                    )
            # occasional weak projectile
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_timer = 200 - (self.boss_index * 4)
                angle_to_player = math.degrees(math.atan2(player_y - self.y, player_x - self.x))
                boss_projectiles.append(
                    Bullet(self.x, self.y, angle_to_player + random.uniform(-8, 8),
                           speed=self.projectile_speed - 2, owner='boss')
                )

        # TYPE 1: shooter-focused
        elif self.type == 1:
            self.attack_timer -= 1
            shoot_interval = max(30, 110 - (self.boss_index * 6))
            if self.attack_timer <= 0:
                self.attack_timer = shoot_interval
                # Shoot a small burst toward player (projectile_count scaled)
                angle_to_player = math.degrees(math.atan2(player_y - self.y, player_x - self.x))
                spread = 10 + (self.boss_index * 1.5)
                for i in range(self.projectile_count):
                    offset = (i - (self.projectile_count - 1) / 2) * (spread / max(1, self.projectile_count))
                    boss_projectiles.append(
                        Bullet(self.x, self.y, angle_to_player + offset, speed=self.projectile_speed, owner='boss')
                    )
            # minimal minion spawning for shooter boss
            self.minion_timer -= 1
            if self.minion_timer <= 0:
                self.minion_timer = 240
                if random.random() < 0.4:
                    enemies.append(
                        GeometricEnemy(self.x + random.uniform(-20, 20),
                                       self.y + random.uniform(-20, 20),
                                       random.choice(['triangle', 'square']),
                                       22)
                    )

        # TYPE 2: mixed
        else:
            self.minion_timer -= 1
            self.attack_timer -= 1
            spawn_interval = max(80, 180 - (self.boss_index * 6))
            shoot_interval = max(60, 150 - (self.boss_index * 5))
            if self.minion_timer <= 0:
                self.minion_timer = spawn_interval
                if random.random() < 0.8:
                    enemies.append(
                        GeometricEnemy(self.x + random.uniform(-25, 25),
                                       self.y + random.uniform(-25, 25),
                                       random.choice(['triangle', 'square']),
                                       22)
                    )
            if self.attack_timer <= 0:
                self.attack_timer = shoot_interval
                angle_to_player = math.degrees(math.atan2(player_y - self.y, player_x - self.x))
                # 1-2 projectiles with small spread
                for i in range(random.randint(1, self.projectile_count)):
                    boss_projectiles.append(
                        Bullet(self.x, self.y, angle_to_player + random.uniform(-12, 12),
                               speed=self.projectile_speed, owner='boss')
                    )

    def hit(self, damage=1):
        self.health -= damage
        return self.health <= 0

    def draw(self, screen):
        # Draw boss polygon
        points = []
        for i in range(self.sides):
            angle_rad = math.radians(self.angle + (360 / self.sides) * i)
            px = self.x + math.cos(angle_rad) * self.size
            py = self.y + math.sin(angle_rad) * self.size
            points.append((px, py))
        
        pygame.draw.polygon(screen, self.color, points, 4)

        # Health bar
        health_ratio = max(0, self.health / self.max_health)
        bar_width = 160
        bar_height = 12
        pygame.draw.rect(screen, RED, (self.x - bar_width/2, self.y - self.size - 30, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN,
                         (self.x - bar_width/2, self.y - self.size - 30, bar_width * health_ratio, bar_height))

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.type = power_type  # 'spread', 'rapid', 'life'
        self.lifetime = 300
        self.radius = 15
        
        if power_type == 'spread':
            self.color = YELLOW
        elif power_type == 'rapid':
            self.color = MAGENTA
        elif power_type == 'life':
            self.color = GREEN
    
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
        self.x = x
        self.y = y
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
        self.reset_game()
    
    def reset_game(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.particles = []
        self.boss = None
        self.boss_projectiles = []
        self.score = 0
        self.wave = 1
        self.game_over = False
        self.wave_complete = False
        self.wave_timer = 0
        self.spawn_wave()
    
    def spawn_wave(self):
        self.wave_complete = False
        self.boss = None  # reset
        self.boss_projectiles = []
        
        # Boss every 3 waves
        if self.wave % 3 == 0:
            # boss_index counts: wave 3 => index 1, wave 6 => 2, ...
            boss_index = self.wave // 3
            # Spawn boss slightly off-screen so it enters play area
            self.boss = BossEnemy(WIDTH // 2, -150, boss_index)
            return
        
        # Otherwise normal wave
        shape_types = ['triangle', 'square', 'pentagon', 'hexagon']
        num_enemies = 3 + self.wave * 2
        for _ in range(num_enemies):
            # Spawn at edges
            side = random.randint(0, 3)
            if side == 0:  # Top
                x, y = random.randint(0, WIDTH), -50
            elif side == 1:  # Right
                x, y = WIDTH + 50, random.randint(0, HEIGHT)
            elif side == 2:  # Bottom
                x, y = random.randint(0, WIDTH), HEIGHT + 50
            else:  # Left
                x, y = -50, random.randint(0, HEIGHT)
            
            shape_type = random.choice(shape_types[:min(len(shape_types), 1 + self.wave // 2)])
            size = random.randint(20, 40)
            enemy = GeometricEnemy(x, y, shape_type, size)
            self.enemies.append(enemy)
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        
        # Mouse aiming - auto-rotate ship to face mouse
        dx = mouse_pos[0] - self.player.x
        dy = mouse_pos[1] - self.player.y
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # Smooth rotation towards mouse
        angle_diff = target_angle - self.player.angle
        # Normalize angle difference to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        # Rotate towards target if far enough
        if abs(angle_diff) > 2:
            if angle_diff > 0:
                self.player.rotate(1)
            else:
                self.player.rotate(-1)
        
        # Keyboard controls (can still be used)
        if keys[pygame.K_LEFT]:
            self.player.rotate(-1)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(1)
        
        # Thrust with keyboard or right mouse button
        if keys[pygame.K_UP] or keys[pygame.K_w] or mouse_buttons[2]:  # Right mouse button
            self.player.thrust()
        
        # Mouse or keyboard shooting
        if mouse_buttons[0] or keys[pygame.K_SPACE]:  # Left mouse button or space
            if self.player.can_shoot():
                self.shoot()
    
    def shoot(self):
        # Make sure shoot_delay matches weapon_type
        if self.player.weapon_type == 'spread':
            self.player.shoot_delay = 10
        elif self.player.weapon_type == 'rapid':
            self.player.shoot_delay = 3
        else:
            self.player.shoot_delay = self.player.default_shoot_delay

        self.player.shoot()
        
        if self.player.weapon_type == 'spread':
            # Shoot 3 bullets in a spread
            for angle_offset in [-15, 0, 15]:
                bullet = Bullet(self.player.x, self.player.y, 
                              self.player.angle + angle_offset, speed=10, owner='player')
                self.bullets.append(bullet)
        elif self.player.weapon_type == 'rapid':
            # Faster shooting, faster bullets
            bullet = Bullet(self.player.x, self.player.y, self.player.angle, speed=15, owner='player')
            self.bullets.append(bullet)
        else:
            # Normal shot
            bullet = Bullet(self.player.x, self.player.y, self.player.angle, speed=10, owner='player')
            self.bullets.append(bullet)
    
    def update(self):
        # Update player
        self.player.update()
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.is_alive():
                try:
                    self.bullets.remove(bullet)
                except ValueError:
                    pass
        
        # Update boss projectiles
        for bproj in self.boss_projectiles[:]:
            bproj.update()
            if not bproj.is_alive():
                try:
                    self.boss_projectiles.remove(bproj)
                except ValueError:
                    pass
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(self.player.x, self.player.y)
        
        # Update boss (if present)
        if self.boss:
            self.boss.update(self.player.x, self.player.y, self.enemies, self.boss_projectiles)
        
        # Update powerups
        for powerup in self.powerups[:]:
            powerup.update()
            if not powerup.is_alive():
                try:
                    self.powerups.remove(powerup)
                except ValueError:
                    pass
        
        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                try:
                    self.particles.remove(particle)
                except ValueError:
                    pass
        
        # Check collisions: player bullets -> boss
        if self.boss:
            for bullet in self.bullets[:]:
                dist = math.sqrt((bullet.x - self.boss.x)**2 + (bullet.y - self.boss.y)**2)
                if dist < self.boss.size:
                    if bullet in self.bullets:
                        try:
                            self.bullets.remove(bullet)
                        except ValueError:
                            pass
                    # damage boss by 1 (or more if you want)
                    if self.boss.hit():
                        # Boss defeated!
                        bonus = 1200 + (self.boss.boss_index * 800)
                        self.score += bonus
                        self.wave_complete = True
                        self.wave_timer = 200
                        # Explosion effect at boss location
                        for _ in range(60):
                            self.particles.append(Particle(self.boss.x + random.uniform(-30,30),
                                                           self.boss.y + random.uniform(-30,30),
                                                           PURPLE))
                        # Drop guaranteed powerup at boss position
                        ptype = random.choice(['spread', 'rapid', 'life'])
                        powerup = PowerUp(self.boss.x, self.boss.y, ptype)
                        self.powerups.append(powerup)
                        self.boss = None
                        # clear boss projectiles (so player won't get hit after boss death)
                        self.boss_projectiles = []
                        break
        
        # Check collisions: player bullets -> enemies
        for bullet in self.bullets[:]:
            hit_something = False
            for enemy in self.enemies[:]:
                dist = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
                if dist < enemy.size:
                    if bullet in self.bullets:
                        try:
                            self.bullets.remove(bullet)
                        except ValueError:
                            pass
                    if enemy.hit():
                        # Enemy destroyed
                        self.score += enemy.sides * 10
                        
                        # Spawn particles
                        for _ in range(8):
                            self.particles.append(Particle(enemy.x, enemy.y, enemy.color))
                        
                        # Split or remove
                        new_enemies = enemy.split()
                        try:
                            self.enemies.remove(enemy)
                        except ValueError:
                            pass
                        self.enemies.extend(new_enemies)
                        
                        # Chance to spawn powerup
                        if random.random() < 0.1:
                            ptype = random.choice(['spread', 'rapid', 'life'])
                            powerup = PowerUp(enemy.x, enemy.y, ptype)
                            self.powerups.append(powerup)
                    hit_something = True
                    break
            if hit_something:
                continue
        
        # Check collisions: boss projectiles -> player
        for bproj in self.boss_projectiles[:]:
            dist = math.sqrt((self.player.x - bproj.x)**2 + (self.player.y - bproj.y)**2)
            if dist < self.player.radius + bproj.radius:
                try:
                    self.boss_projectiles.remove(bproj)
                except ValueError:
                    pass
                if self.player.invulnerable == 0:
                    self.player.lives -= 1
                    self.player.invulnerable = 100
                    # explode particles
                    for _ in range(18):
                        self.particles.append(Particle(self.player.x, self.player.y, CYAN))
                    if self.player.lives <= 0:
                        self.game_over = True
                    break
        
        # Check player-enemy collisions
        if self.player.invulnerable == 0:
            for enemy in self.enemies[:]:
                dist = math.sqrt((self.player.x - enemy.x)**2 + (self.player.y - enemy.y)**2)
                if dist < enemy.size + self.player.radius:
                    self.player.lives -= 1
                    self.player.invulnerable = 120
                    
                    # Explosion particles
                    for _ in range(20):
                        self.particles.append(Particle(self.player.x, self.player.y, CYAN))
                    
                    if self.player.lives <= 0:
                        self.game_over = True
                    break
        
        # Check player-powerup collisions
        for powerup in self.powerups[:]:
            dist = math.sqrt((self.player.x - powerup.x)**2 + (self.player.y - powerup.y)**2)
            if dist < powerup.radius + self.player.radius:
                try:
                    self.powerups.remove(powerup)
                except ValueError:
                    pass
                
                if powerup.type == 'life':
                    self.player.lives += 1
                    self.score += 100
                else:
                    self.player.weapon_type = powerup.type
                    self.player.weapon_timer = 300
                
                # Particles
                for _ in range(15):
                    self.particles.append(Particle(powerup.x, powerup.y, powerup.color))
        
        # Check wave completion
        # For boss waves: boss must be None and no enemies (minions) and no boss projectiles remain
        if self.boss is None and not self.enemies and not self.boss_projectiles and not self.wave_complete:
            # Normal wave finished
            self.wave_complete = True
            self.wave_timer = 120
            self.wave += 1
            self.score += self.wave * 100
        
        if self.wave_complete:
            self.wave_timer -= 1
            if self.wave_timer <= 0:
                self.spawn_wave()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw grid
        for x in range(0, WIDTH, 50):
            pygame.draw.line(self.screen, (20, 20, 40), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(self.screen, (20, 20, 40), (0, y), (WIDTH, y), 1)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw boss (if present)
        if self.boss:
            self.boss.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        # Draw boss projectiles
        for bproj in self.boss_projectiles:
            bproj.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw UI
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        wave_text = self.small_font.render(f"Wave: {self.wave}", True, CYAN)
        lives_text = self.small_font.render(f"Lives: {self.player.lives}", True, GREEN)
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(wave_text, (10, 40))
        self.screen.blit(lives_text, (10, 70))
        
        # Weapon indicator
        if self.player.weapon_timer > 0:
            weapon_text = self.small_font.render(f"Weapon: {self.player.weapon_type.upper()}", 
                                                 True, YELLOW)
            self.screen.blit(weapon_text, (10, 100))
            time_left = self.player.weapon_timer // 60
            timer_text = self.small_font.render(f"Time: {time_left}s", True, WHITE)
            self.screen.blit(timer_text, (10, 125))
        
        # Wave complete
        if self.wave_complete and self.wave_timer > 60:
            complete_text = self.font.render("WAVE COMPLETE!", True, GREEN)
            self.screen.blit(complete_text, 
                           (WIDTH // 2 - complete_text.get_width() // 2, HEIGHT // 2))
        
        # Draw crosshair at mouse position
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, WHITE, mouse_pos, 8, 1)
        pygame.draw.line(self.screen, WHITE, (mouse_pos[0] - 12, mouse_pos[1]), 
                        (mouse_pos[0] - 4, mouse_pos[1]), 2)
        pygame.draw.line(self.screen, WHITE, (mouse_pos[0] + 4, mouse_pos[1]), 
                        (mouse_pos[0] + 12, mouse_pos[1]), 2)
        pygame.draw.line(self.screen, WHITE, (mouse_pos[0], mouse_pos[1] - 12), 
                        (mouse_pos[0], mouse_pos[1] - 4), 2)
        pygame.draw.line(self.screen, WHITE, (mouse_pos[0], mouse_pos[1] + 4), 
                        (mouse_pos[0], mouse_pos[1] + 12), 2)
        
        # Instructions
        inst = self.small_font.render("W: Thrust | Mouse: Aim & Shoot | SPACE: Shoot", True, (150, 150, 150))
        self.screen.blit(inst, (WIDTH // 2 - 170, HEIGHT - 25))
        
        pygame.display.flip()
    
    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        wave_text = self.small_font.render(f"Wave Reached: {self.wave}", True, CYAN)
        restart_text = self.small_font.render("Press SPACE to restart", True, WHITE)
        
        center_x = WIDTH // 2
        
        self.screen.blit(game_over_text, 
                        (center_x - game_over_text.get_width() // 2, HEIGHT // 2 - 70))
        self.screen.blit(score_text, 
                        (center_x - score_text.get_width() // 2, HEIGHT // 2 - 10))
        self.screen.blit(wave_text, 
                        (center_x - wave_text.get_width() // 2, HEIGHT // 2 + 30))
        self.screen.blit(restart_text, 
                        (center_x - restart_text.get_width() // 2, HEIGHT // 2 + 70))
        
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
            
            if not self.game_over:
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
