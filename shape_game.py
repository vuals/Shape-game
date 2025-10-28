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

[Previous classes and code omitted for brevity]

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
        self.coins = 0
        self.wave = 1
        self.game_over = False
        self.wave_complete = False
        self.wave_timer = 0
        self.shop_open = False
        self.owned_upgrades = {}
        # Shop items: id, name, cost, description
        self.shop_items = [
            {'id': 'speed', 'name': 'Increase Speed', 'cost': 150, 'desc': '+1 max speed'},
            {'id': 'damage', 'name': 'Increase Damage', 'cost': 200, 'desc': '+1 bullet damage'},
            {'id': 'firerate', 'name': 'Faster Fire', 'cost': 180, 'desc': '-1 shoot delay'},
            {'id': 'life', 'name': 'Extra Life', 'cost': 250, 'desc': '+1 life'}
        ]
        self.shop_rects = []  # store clickable areas
        self.spawn_wave()

    def draw_shop_overlay(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 6, 8, 200))
        self.screen.blit(overlay, (0,0))
        
        # Shop window
        box_w, box_h = 540, 300
        box_x = WIDTH//2 - box_w//2
        box_y = HEIGHT//2 - box_h//2
        pygame.draw.rect(self.screen, (20,20,30), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(self.screen, CYAN, (box_x, box_y, box_w, box_h), 3)
        
        # Title and coins
        title = self.font.render("SHOP", True, WHITE)
        coins = self.small_font.render(f"Coins: {self.coins}", True, YELLOW)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, box_y + 12))
        self.screen.blit(coins, (WIDTH//2 - coins.get_width()//2, box_y + 50))
        
        # Draw items in a 2x2 grid
        self.shop_rects.clear()
        gap = 16
        cols = 2
        card_w = (box_w - gap*(cols+1))//cols
        card_h = 100
        for idx, item in enumerate(self.shop_items):
            r = idx // cols
            c = idx % cols
            rx = box_x + gap + c*(card_w + gap)
            ry = box_y + 60 + r*(card_h + gap)
            rect = pygame.Rect(rx, ry, card_w, card_h)
            pygame.draw.rect(self.screen, (14,14,18), rect)
            if self.coins >= item['cost']:
                border_color = GREEN
            else:
                border_color = WHITE
            pygame.draw.rect(self.screen, border_color, rect, 2)
            name = self.small_font.render(item['name'], True, WHITE)
            desc = self.small_font.render(item['desc'], True, (180,180,180))
            cost = self.small_font.render(f"Cost: {item['cost']}", True, YELLOW)
            self.screen.blit(name, (rx+8, ry+8))
            self.screen.blit(desc, (rx+8, ry+36))
            self.screen.blit(cost, (rx+8, ry+64))
            self.shop_rects.append((rect, item))
        
        inst = self.small_font.render("Click an item to buy. Press S to close.", True, (180,180,180))
        self.screen.blit(inst, (WIDTH//2 - inst.get_width()//2, box_y + box_h - 28))

    def draw_game_background(self):
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
        coins_text = self.small_font.render(f"Coins: {self.coins}", True, YELLOW)
        shop_hint = self.small_font.render("Press S for Shop", True, (150,150,150))
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(wave_text, (10, 40))
        self.screen.blit(lives_text, (10, 70))
        self.screen.blit(coins_text, (10, 100))
        self.screen.blit(shop_hint, (10, HEIGHT - 50))
        
        # Weapon indicator
        if self.player.weapon_timer > 0:
            weapon_text = self.small_font.render(f"Weapon: {self.player.weapon_type.upper()}", True, YELLOW)
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

    def draw(self):
        # Always draw game background
        self.draw_game_background()
        
        # Draw shop overlay if shop is open
        if self.shop_open:
            self.draw_shop_overlay()
        
        # Update display
        pygame.display.flip()

    def update(self):
        # Don't update game state if shop is open
        if self.shop_open:
            return
            
        # [Rest of the update method remains the same]

    def handle_input(self):
        # If shop is open, don't process gameplay input
        if self.shop_open:
            return
        
        # [Rest of handle_input method remains the same]

    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.game_over:
                        self.reset_game()
                    elif event.key == pygame.K_s:
                        self.shop_open = not self.shop_open
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left click
                        if self.shop_open:
                            mx, my = event.pos
                            for rect, item in self.shop_rects:
                                if rect.collidepoint(mx, my):
                                    # Try to buy the item
                                    if self.coins >= item['cost']:
                                        self.coins -= item['cost']
                                        # Apply upgrade effects
                                        if item['id'] == 'speed':
                                            self.player.max_speed += 1
                                        elif item['id'] == 'damage':
                                            self.player.damage += 1
                                        elif item['id'] == 'firerate':
                                            self.player.default_shoot_delay = max(1, self.player.default_shoot_delay - 1)
                                        elif item['id'] == 'life':
                                            self.player.lives += 1
                                        # Track purchase
                                        self.owned_upgrades[item['id']] = self.owned_upgrades.get(item['id'], 0) + 1
                                    break
            
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