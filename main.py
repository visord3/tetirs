import sys
import pygame
import math
import random

# Import centralized sound system
from sound_manager import load_game_sounds, play_sound, play_music, stop_music

def safe_get_events():
    """Safely get pygame events with fallback"""
    try:
        return pygame.event.get()
    except (SystemError, pygame.error):
        try:
            pygame.event.clear()
            pygame.event.pump()
            return []
        except:
            return []
    except Exception:
        return []

# Initialize pygame
pygame.init()
pygame.mixer.init()
pygame.joystick.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors - Centralized color definitions
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
HIGHLIGHT = (100, 100, 255)
TITLE_COLOR = (255, 255, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Setup display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Tetris")

# Fonts
title_font = pygame.font.SysFont("Arial", 72, bold=True)
menu_font = pygame.font.SysFont("Arial", 48)
info_font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)

# Background particles for menu
class Particle:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.size = random.randint(1, 3)
        self.color = random.choice([CYAN, YELLOW, MAGENTA, GREEN, RED, BLUE, ORANGE])
        self.alpha = random.randint(50, 200)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around screen
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = SCREEN_HEIGHT
        elif self.y > SCREEN_HEIGHT:
            self.y = 0
    
    def draw(self, surface):
        pygame.draw.circle(surface, (*self.color, self.alpha), (int(self.x), int(self.y)), self.size)

# Animated menu button class
class MenuButton:
    def __init__(self, text, x, y, width, height, callback=None):
        self.text = text
        self.base_rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.rect = self.base_rect.copy()
        self.callback = callback
        self.hover = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.glow = 0
        self.selected = False
        
    def update(self, mouse_pos, dt):
        # Check if mouse is over button
        self.hover = self.rect.collidepoint(mouse_pos)
        
        # Update scale animation
        if self.hover or self.selected:
            self.target_scale = 1.1
        else:
            self.target_scale = 1.0
        
        # Smooth scale transition
        self.scale += (self.target_scale - self.scale) * 0.2
        
        # Update rectangle based on scale
        scaled_width = int(self.base_rect.width * self.scale)
        scaled_height = int(self.base_rect.height * self.scale)
        self.rect = pygame.Rect(
            self.base_rect.centerx - scaled_width // 2,
            self.base_rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        # Glow effect
        if self.hover or self.selected:
            self.glow = min(self.glow + dt * 0.01, 1.0)
        else:
            self.glow = max(self.glow - dt * 0.01, 0.0)
    
    def draw(self, surface):
        # Draw glow effect
        if self.glow > 0:
            glow_surface = pygame.Surface((self.rect.width + 40, self.rect.height + 40), pygame.SRCALPHA)
            glow_color = (*HIGHLIGHT, int(100 * self.glow))
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=20)
            surface.blit(glow_surface, (self.rect.x - 20, self.rect.y - 20))
        
        # Draw button background
        button_color = HIGHLIGHT if (self.hover or self.selected) else LIGHT_GRAY
        pygame.draw.rect(surface, button_color, self.rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=15)
        
        # Draw text with shadow
        text_shadow = menu_font.render(self.text, True, BLACK)
        text_surface = menu_font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surface, text_rect)
    
    def handle_click(self):
        if self.callback:
            self.callback()

# Controller manager
class ControllerManager:
    def __init__(self):
        self.controller = None
        self.reconnect_timer = 0
        self.check_controller()
    
    def check_controller(self):
        """Check for connected controllers"""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            print(f"Controller connected: {self.controller.get_name()}")
            return True
        else:
            self.controller = None
            return False
    
    def update(self, dt):
        """Periodically check for controller reconnection"""
        if not self.controller:
            self.reconnect_timer += dt
            if self.reconnect_timer >= 3000:  # Check every 3 seconds
                self.reconnect_timer = 0
                self.check_controller()
    
    def get_controller(self):
        return self.controller

# Global controller manager
controller_manager = ControllerManager()

def start_single_player():
    """Start single player game"""
    from single_player import SinglePlayerGame
    game = SinglePlayerGame(controller_manager.get_controller())
    game.run(screen)
    # Return to main menu after game ends
    main_menu()

def start_multiplayer():
    """Start multiplayer game"""
    from multiplayer import multiplayer_mode
    multiplayer_mode()
    # Return to main menu after game ends
    main_menu()

def show_settings():
    """Show settings menu"""
    settings_menu()

def main_menu():
    """Enhanced interactive main menu"""
    clock = pygame.time.Clock()
    running = True
    
    # Create particles for background effect
    particles = [Particle() for _ in range(50)]
    
    # Create animated menu buttons
    buttons = [
        MenuButton("Single Player", SCREEN_WIDTH // 2, 250, 300, 60, start_single_player),
        MenuButton("Multiplayer", SCREEN_WIDTH // 2, 330, 300, 60, start_multiplayer),
        MenuButton("Settings", SCREEN_WIDTH // 2, 410, 300, 60, show_settings),
        MenuButton("Quit", SCREEN_WIDTH // 2, 490, 300, 60, lambda: sys.exit())
    ]
    
    selected_index = 0
    buttons[selected_index].selected = True
    
    # Animation variables
    title_offset = 0
    title_time = 0
    
    # Start playing menu music (ensure it always starts when entering menu)
    play_music()
    
    while running:
        dt = clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        
        # Update controller manager
        controller_manager.update(dt)
        
        # Handle events using safe_get_events
        for event in safe_get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Mouse controls
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        play_sound("menu_select")
                        # Stop music if leaving menu
                        stop_music()
                        button.handle_click()
                        return
            
            # Keyboard controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    buttons[selected_index].selected = False
                    selected_index = (selected_index - 1) % len(buttons)
                    buttons[selected_index].selected = True
                    play_sound("menu_select")
                elif event.key == pygame.K_DOWN:
                    buttons[selected_index].selected = False
                    selected_index = (selected_index + 1) % len(buttons)
                    buttons[selected_index].selected = True
                    play_sound("menu_select")
                elif event.key == pygame.K_RETURN:
                    play_sound("menu_select")
                    # Stop music if leaving menu
                    stop_music()
                    buttons[selected_index].handle_click()
                    return
                elif event.key == pygame.K_ESCAPE:
                    return
            
            # Controller controls
            if controller_manager.controller:
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = controller_manager.controller.get_hat(0)
                    if hat_y == 1:  # Up
                        buttons[selected_index].selected = False
                        selected_index = (selected_index - 1) % len(buttons)
                        buttons[selected_index].selected = True
                        play_sound("menu_move")
                    elif hat_y == -1:  # Down
                        buttons[selected_index].selected = False
                        selected_index = (selected_index + 1) % len(buttons)
                        buttons[selected_index].selected = True
                        play_sound("menu_move")
                
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0:  # X button
                        play_sound("menu_select")
                        # Stop music if leaving menu
                        stop_music()
                        buttons[selected_index].handle_click()
                        return
        
        # Update particles
        for particle in particles:
            particle.update()
        
        # Update buttons
        for i, button in enumerate(buttons):
            # Check mouse hover
            if button.rect.collidepoint(mouse_pos) and not button.selected:
                if not button.hover:
                    play_sound("menu_select")
                buttons[selected_index].selected = False
                selected_index = i
                button.selected = True
            button.update(mouse_pos, dt)
        
        # Update title animation
        title_time += dt * 0.001
        title_offset = math.sin(title_time) * 10
        
        # Clear screen
        screen.fill(GRAY)
        
        # Draw particles
        for particle in particles:
            particle.draw(screen)
        
        # Draw animated title
        title_surface = title_font.render("TETRIS", True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100 + title_offset))
        
        # Title shadow
        shadow_surface = title_font.render("TETRIS", True, BLACK)
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 3, 100 + title_offset + 3))
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(title_surface, title_rect)
        
        # Draw buttons
        for button in buttons:
            button.draw(screen)
        
        # Draw controller status
        if controller_manager.controller:
            status_text = info_font.render(f"Controller: {controller_manager.controller.get_name()}", True, WHITE)
        else:
            status_text = info_font.render("No controller connected", True, WHITE)
        screen.blit(status_text, (20, SCREEN_HEIGHT - 30))
        
        # Draw version info
        version_text = small_font.render("v1.0", True, WHITE)
        screen.blit(version_text, (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()

def settings_menu():
    """Settings menu"""
    clock = pygame.time.Clock()
    running = True
    
    buttons = [
        MenuButton(f"Sound: {'ON' if pygame.mixer.music.get_volume() > 0 else 'OFF'}", 
                   SCREEN_WIDTH // 2, 250, 300, 60),
        MenuButton("Back", SCREEN_WIDTH // 2, 350, 300, 60)
    ]
    
    selected_index = 0
    buttons[selected_index].selected = True
    
    while running:
        dt = clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    buttons[selected_index].selected = False
                    selected_index = (selected_index - 1) % len(buttons)
                    buttons[selected_index].selected = True
                    play_sound("menu_select")
                elif event.key == pygame.K_DOWN:
                    buttons[selected_index].selected = False
                    selected_index = (selected_index + 1) % len(buttons)
                    buttons[selected_index].selected = True
                    play_sound("menu_select")
                elif event.key == pygame.K_RETURN:
                    if selected_index == 0:  # Toggle sound
                        if pygame.mixer.music.get_volume() > 0:
                            pygame.mixer.music.set_volume(0.0)
                            buttons[0].text = "Sound: OFF"
                        else:
                            pygame.mixer.music.set_volume(0.7)
                            buttons[0].text = "Sound: ON"
                        play_sound("menu_select")
                    elif selected_index == 1:  # Back
                        return
                elif event.key == pygame.K_ESCAPE:
                    return
        
        # Update buttons
        for button in buttons:
            button.update(mouse_pos, dt)
        
        # Clear screen
        screen.fill(GRAY)
        
        # Draw title
        title_surface = menu_font.render("SETTINGS", True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)
        
        # Draw buttons
        for button in buttons:
            button.draw(screen)
        
        pygame.display.flip()

def main():
    """Main entry point"""
    main_menu()

if __name__ == "__main__":
    main()