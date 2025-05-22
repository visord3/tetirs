# multiplayer.py - Improved multiplayer mode with proper game loop
import sys
import pygame
import random
import os

# Import game components
from grid import Grid
from colors import Colors
from constants import *
from player import Player

# Add missing color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)

# Add missing get_random_block function
def get_random_block(cell_size):
    """Generate a random tetromino - placeholder implementation"""
    from blocks import IBlock, OBlock, TBlock, SBlock, ZBlock, JBlock, LBlock
    blocks = [IBlock, OBlock, TBlock, SBlock, ZBlock, JBlock, LBlock]
    block_class = random.choice(blocks)
    return block_class(cell_size)

from sound_manager import load_game_sounds, play_sound, play_music, stop_music, ensure_music_playing

# Game constants
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PREVIEW_SIZE = 4
LEVEL_SPEED = [1000, 800, 600, 500, 400, 300, 250, 200, 150, 100]

# Layout constants
PANEL_WIDTH = 220
PANEL_MARGIN = 30
FIELD_MARGIN = 40
OUTER_MARGIN = 40
INFO_PADDING = 20
NEXT_BOX_SIZE = 4 * CELL_SIZE + 2 * INFO_PADDING
PANEL_HEIGHT = max(GRID_HEIGHT * CELL_SIZE, 350)


class Player:
    """Represents a player in multiplayer mode"""
    def __init__(self, player_id, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT):
        self.player_id = player_id
        self.grid = Grid(grid_width, grid_height, CELL_SIZE)
        self.current_block = None
        self.next_block = None
        
        # Game stats
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.active = True
        
        # Timing
        self.fall_speed = LEVEL_SPEED[0]
        self.last_drop_time = pygame.time.get_ticks()
        self.last_move_time = pygame.time.get_ticks()
        
        # Input state
        self.left_pressed = False
        self.right_pressed = False
        self.down_pressed = False
        
        # Fonts
        self.font_big = pygame.font.SysFont("Arial", 36)
        self.font_medium = pygame.font.SysFont("Arial", 24)
        self.font_small = pygame.font.SysFont("Arial", 18)
        
        # Spawn initial blocks
        self.spawn_block()
        self.spawn_block()
    
    def draw_info(self, screen, offset_x, offset_y):
        """Draw player information and score"""
        # Draw score panel background
        score_bg = pygame.Surface((200, 150))
        score_bg.fill(GRAY)
        pygame.draw.rect(score_bg, WHITE, score_bg.get_rect(), 2)
        
        # Draw player label
        player_text = self.font_big.render(f"Player {self.player_id}", True, WHITE)
        player_rect = player_text.get_rect(center=(100, 30))
        score_bg.blit(player_text, player_rect)
        
        # Draw score
        score_text = self.font_medium.render(f"Score: {self.score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(100, 70))
        score_bg.blit(score_text, score_rect)
        
        # Draw level
        level_text = self.font_medium.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(100, 100))
        score_bg.blit(level_text, level_rect)
        
        # Draw the score panel
        screen.blit(score_bg, (offset_x, offset_y))
    
    def spawn_block(self):
        """Spawn a new tetromino"""
        if self.next_block:
            self.current_block = self.next_block
        else:
            self.current_block = get_random_block(CELL_SIZE)
        
        # Generate next block
        self.next_block = get_random_block(CELL_SIZE)
        
        # Center the block
        self.current_block.col_offset = self.grid.num_cols // 2 - 2
        self.current_block.row_offset = 0
        
        # Check if block can be placed
        if not self.current_block.is_valid_position(self.grid):
            self.active = False
            play_sound("game_over")
    
    def update(self, current_time):
        """Update player state"""
        if not self.active:
            return
        
        # Handle automatic drop
        if current_time - self.last_drop_time >= self.fall_speed:
            self.drop_block()
            self.last_drop_time = current_time
    
    def drop_block(self):
        """Move block down one step"""
        if not self.active or not self.current_block:
            return False
        
        if not self.current_block.move(1, 0, self.grid):
            # Lock the block
            return self.lock_block()
        return True
    
    def move(self, dx, dy):
        """Move the current block"""
        if self.active and self.current_block:
            if self.current_block.move(dy, dx, self.grid):
                play_sound("move")
                return True
        return False
    
    def rotate(self):
        """Rotate the current block"""
        if self.active and self.current_block:
            if self.current_block.rotate(self.grid):
                play_sound("rotate")
                return True
        return False
    
    def hard_drop(self):
        """Drop block to bottom instantly"""
        if not self.active or not self.current_block:
            return
        
        drop_count = 0
        while self.current_block.move(1, 0, self.grid):
            drop_count += 1
            self.score += 2  # 2 points per cell
        
        self.lock_block()
    
    def handle_continuous_movement(self, current_time, move_delay):
        """Handle held key movement"""
        if not self.active or not self.current_block:
            return
        
        if current_time - self.last_move_time <= move_delay:
            return
        
        if self.left_pressed:
            if self.move(-1, 0):
                self.last_move_time = current_time
        elif self.right_pressed:
            if self.move(1, 0):
                self.last_move_time = current_time
        elif self.down_pressed:
            if self.drop_block():
                self.score += 1  # 1 point per soft drop
                self.last_move_time = current_time
    
    def lock_block(self):
        """Lock block in place and spawn new one"""
        if not self.current_block:
            return False
        
        # Place block on grid
        self.grid.place_block(self.current_block)
        play_sound("drop")
        
        # Clear rows
        rows_cleared = self.grid.clear_rows()
        if rows_cleared > 0:
            play_sound("clear")
            self.lines_cleared += rows_cleared
            self.score += rows_cleared * rows_cleared * 100 * self.level
            old_level = self.level
            self.level = min(10, self.lines_cleared // 10 + 1)
            if self.level > old_level:
                play_sound("level_up")
            self.fall_speed = LEVEL_SPEED[min(9, self.level - 1)]
        
        # Spawn new block
        self.spawn_block()
        return True

    def draw_current_block(self, screen, offset_x, offset_y):
        """Draw the current falling block on the grid"""
        if self.active and self.current_block:
            self.current_block.draw(screen, offset_x, offset_y)
            
    def draw_next_piece(self, screen, offset_x, offset_y):
        """Draw the next piece preview"""
        if self.next_block:
            # Draw next piece label
            preview_text = self.font_medium.render("Next:", True, WHITE)
            screen.blit(preview_text, (offset_x, offset_y))
            
            # Create preview surface
            preview_surface = pygame.Surface((PREVIEW_SIZE * CELL_SIZE, PREVIEW_SIZE * CELL_SIZE))
            preview_surface.fill(GRAY)
            pygame.draw.rect(preview_surface, WHITE, preview_surface.get_rect(), 2)
            
            # Draw the next block centered in preview
            original_offsets = (self.next_block.row_offset, self.next_block.col_offset)
            self.next_block.row_offset = 1
            self.next_block.col_offset = 1
            self.next_block.draw(preview_surface, 0, 0)
            
            # Restore original offsets
            self.next_block.row_offset, self.next_block.col_offset = original_offsets
            
            # Draw the preview surface
            screen.blit(preview_surface, (offset_x, offset_y + 30))


def show_end_screen(screen, winner, player1_score, player2_score):
    """Display end screen with winner and option to play again"""
    font_big = pygame.font.SysFont("Arial", 48)
    font_medium = pygame.font.SysFont("Arial", 36)
    font_small = pygame.font.SysFont("Arial", 24)
    
    clock = pygame.time.Clock()
    selected_option = 0  # 0 = Play Again, 1 = Main Menu
    
    # Initialize controller if available
    controller = None
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
    
    while True:
        dt = clock.tick(60)
        
        # Clear screen
        screen.fill(GRAY)
        
        # Draw winner announcement
        if winner == "tie":
            title_text = font_big.render("It's a Tie!", True, WHITE)
        else:
            title_text = font_big.render(f"{winner} Wins!", True, WHITE)
        title_rect = title_text.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Draw scores
        score_text = font_medium.render(f"Player 1: {player1_score:,}  |  Player 2: {player2_score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(screen.get_width() // 2, 220))
        screen.blit(score_text, score_rect)
        
        # Draw options
        play_again_color = (100, 100, 255) if selected_option == 0 else WHITE
        main_menu_color = (100, 100, 255) if selected_option == 1 else WHITE
        
        play_again_text = font_medium.render("Play Again", True, play_again_color)
        play_again_rect = play_again_text.get_rect(center=(screen.get_width() // 2, 320))
        screen.blit(play_again_text, play_again_rect)
        
        main_menu_text = font_medium.render("Main Menu", True, main_menu_color)
        main_menu_rect = main_menu_text.get_rect(center=(screen.get_width() // 2, 380))
        screen.blit(main_menu_text, main_menu_rect)
        
        # Draw controls
        controls_text = font_small.render("↑↓: Select | Enter: Confirm", True, (200, 200, 200))
        controls_rect = controls_text.get_rect(center=(screen.get_width() // 2, 480))
        screen.blit(controls_text, controls_rect)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_music()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    selected_option = 1 - selected_option
                    play_sound("menu_select")
                elif event.key == pygame.K_RETURN:
                    play_sound("menu_select")
                    return selected_option == 0  # True for play again, False for main menu
                elif event.key == pygame.K_ESCAPE:
                    return False  # Return to main menu
            
            # Controller support
            if controller:
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = controller.get_hat(0)
                    if hat_y != 0:
                        selected_option = 1 - selected_option
                        play_sound("menu_select")
                
                if event.type == pygame.JOYBUTTONDOWN:
                    if controller.get_button(0):  # X button
                        play_sound("menu_select")
                        return selected_option == 0
        
        pygame.display.flip()


def multiplayer_mode():
    """Run multiplayer Tetris game"""
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    
    # Load sounds
    load_game_sounds()
    
    # Play background music
    play_music()
    
    # Setup display
    window_width = (OUTER_MARGIN * 2 +
                    2 * GRID_WIDTH * CELL_SIZE +
                    2 * PANEL_WIDTH +
                    2 * PANEL_MARGIN +
                    FIELD_MARGIN)
    window_height = OUTER_MARGIN * 2 + PANEL_HEIGHT
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Tetris - Multiplayer")
    
    # Create players
    player1 = Player(1)
    player2 = Player(2)
    
    # Game loop variables
    clock = pygame.time.Clock()
    running = True
    move_delay = 100  # ms between moves when holding a direction
    
    # Center both grids and info panels as a group
    grid1_x = OUTER_MARGIN
    panel1_x = grid1_x + GRID_WIDTH * CELL_SIZE + PANEL_MARGIN
    grid2_x = panel1_x + PANEL_WIDTH + FIELD_MARGIN
    panel2_x = grid2_x + GRID_WIDTH * CELL_SIZE + PANEL_MARGIN
    grid_y = OUTER_MARGIN
    panel_y = OUTER_MARGIN
    score_y = panel_y + INFO_PADDING
    next_y = score_y + 100 + INFO_PADDING
    controls_y = next_y + NEXT_BOX_SIZE + INFO_PADDING
    
    while running:
        current_time = pygame.time.get_ticks()
        
        # Check if music should be playing
        ensure_music_playing()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                stop_music()
            
            # Player 1 controls (WASD + QE)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    player1.left_pressed = True
                elif event.key == pygame.K_d:
                    player1.right_pressed = True
                elif event.key == pygame.K_s:
                    player1.down_pressed = True
                elif event.key == pygame.K_w:
                    player1.rotate()
                elif event.key == pygame.K_SPACE:
                    player1.hard_drop()
                elif event.key == pygame.K_ESCAPE:
                    running = False
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    player1.left_pressed = False
                elif event.key == pygame.K_d:
                    player1.right_pressed = False
                elif event.key == pygame.K_s:
                    player1.down_pressed = False
            
            # Player 2 controls (Arrow keys + P)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player2.left_pressed = True
                elif event.key == pygame.K_RIGHT:
                    player2.right_pressed = True
                elif event.key == pygame.K_DOWN:
                    player2.down_pressed = True
                elif event.key == pygame.K_UP:
                    player2.rotate()
                elif event.key == pygame.K_RETURN:
                    player2.hard_drop()
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    player2.left_pressed = False
                elif event.key == pygame.K_RIGHT:
                    player2.right_pressed = False
                elif event.key == pygame.K_DOWN:
                    player2.down_pressed = False
        
        # Update players
        player1.update(current_time)
        player2.update(current_time)
        
        # Handle continuous movement
        player1.handle_continuous_movement(current_time, move_delay)
        player2.handle_continuous_movement(current_time, move_delay)
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw player 1's grid and info
        player1.grid.draw(screen, grid1_x, grid_y)
        player1.draw_current_block(screen, grid1_x, grid_y)
        player1.draw_info(screen, panel1_x, panel_y)
        player1.draw_next_piece(screen, panel1_x + INFO_PADDING, next_y)
        font = pygame.font.SysFont("Arial", 18)
        controls = ["Controls:", "A/D: Move", "W: Rotate", "S: Down", "Space: Hard Drop"]
        for i, line in enumerate(controls):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (panel1_x + INFO_PADDING, controls_y + i * 24))
        
        # Draw player 2's grid and info
        player2.grid.draw(screen, grid2_x, grid_y)
        player2.draw_current_block(screen, grid2_x, grid_y)
        player2.draw_info(screen, panel2_x, panel_y)
        player2.draw_next_piece(screen, panel2_x + INFO_PADDING, next_y)
        controls2 = ["Controls:", "←/→: Move", "↑: Rotate", "↓: Down", "Enter: Hard Drop"]
        for i, line in enumerate(controls2):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (panel2_x + INFO_PADDING, controls_y + i * 24))
        
        # Check for game over
        if not player1.active or not player2.active:
            winner = "Player 1" if player2.active else "Player 2" if player1.active else "tie"
            show_end_screen(screen, winner, player1.score, player2.score)
            running = False
        
        pygame.display.flip()
        clock.tick(60)
    
    # Stop music when quitting
    stop_music()
    pygame.quit()