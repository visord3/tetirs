# multiplayer.py - Improved multiplayer mode with proper game loop
import sys
import pygame
import random
import os

# Import game components
from grid import Grid
from colors import Colors

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
        
        # Spawn initial blocks
        self.spawn_block()
        self.spawn_block()
    
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
            self.level = min(10, self.lines_cleared // 10 + 1)
            self.fall_speed = LEVEL_SPEED[min(9, self.level - 1)]
        
        # Spawn new block
        self.spawn_block()
        return True
    
    def move(self, dx, dy):
        """Move the current block"""
        if self.active and self.current_block:
            return self.current_block.move(dy, dx, self.grid)
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
    """Main multiplayer game mode"""
    # Constants
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    GAME_DURATION = 120000  # 2 minutes in milliseconds
    
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multiplayer Tetris")
    
    # Initialize controller
    controller = None
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
        print(f"Controller connected: {controller.get_name()}")
    
    # Initialize sounds
    load_game_sounds()
    play_music(volume=0.5)
    
    # Main game loop - allows replaying without recursion
    play_again = True
    while play_again:
        # Create players
        player1 = Player(1)
        player2 = Player(2)
        
        # Game state
        clock = pygame.time.Clock()
        running = True
        start_time = pygame.time.get_ticks()
        move_delay = 100
        
        # Fonts
        font_big = pygame.font.SysFont("Arial", 36)
        font_medium = pygame.font.SysFont("Arial", 24)
        font_small = pygame.font.SysFont("Arial", 18)
        
        # Game loop
        while running:
            ensure_music_playing()
            
            current_time = pygame.time.get_ticks()
            elapsed_time = current_time - start_time
            remaining_time = max(0, GAME_DURATION - elapsed_time)
            
            # Check game over conditions
            if remaining_time == 0 or (not player1.active and not player2.active):
                running = False
                break
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stop_music()
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        stop_music()
                        return  # Return to main menu
                    
                    # Player 1 controls (arrows)
                    if player1.active and player1.current_block:
                        if event.key == pygame.K_LEFT:
                            player1.left_pressed = True
                            player1.move(-1, 0)
                            player1.last_move_time = current_time
                        elif event.key == pygame.K_RIGHT:
                            player1.right_pressed = True
                            player1.move(1, 0)
                            player1.last_move_time = current_time
                        elif event.key == pygame.K_DOWN:
                            player1.down_pressed = True
                            player1.drop_block()
                            player1.last_move_time = current_time
                        elif event.key == pygame.K_UP:
                            player1.rotate()
                        elif event.key == pygame.K_RSHIFT:
                            player1.hard_drop()
                    
                    # Player 2 controls (WASD)
                    if player2.active and player2.current_block:
                        if event.key == pygame.K_a:
                            player2.left_pressed = True
                            player2.move(-1, 0)
                            player2.last_move_time = current_time
                        elif event.key == pygame.K_d:
                            player2.right_pressed = True
                            player2.move(1, 0)
                            player2.last_move_time = current_time
                        elif event.key == pygame.K_s:
                            player2.down_pressed = True
                            player2.drop_block()
                            player2.last_move_time = current_time
                        elif event.key == pygame.K_w:
                            player2.rotate()
                        elif event.key == pygame.K_SPACE:
                            player2.hard_drop()
                
                elif event.type == pygame.KEYUP:
                    # Player 1
                    if event.key == pygame.K_LEFT:
                        player1.left_pressed = False
                    elif event.key == pygame.K_RIGHT:
                        player1.right_pressed = False
                    elif event.key == pygame.K_DOWN:
                        player1.down_pressed = False
                    
                    # Player 2
                    elif event.key == pygame.K_a:
                        player2.left_pressed = False
                    elif event.key == pygame.K_d:
                        player2.right_pressed = False
                    elif event.key == pygame.K_s:
                        player2.down_pressed = False
                
                # Controller support for Player 1
                if controller and player1.active and player1.current_block:
                    if event.type == pygame.JOYHATMOTION:
                        hat_x, hat_y = controller.get_hat(0)
                        player1.left_pressed = (hat_x == -1)
                        player1.right_pressed = (hat_x == 1)
                        player1.down_pressed = (hat_y == -1)
                        
                        if hat_x == -1:
                            player1.move(-1, 0)
                        elif hat_x == 1:
                            player1.move(1, 0)
                        if hat_y == -1:
                            player1.drop_block()
                    
                    if event.type == pygame.JOYBUTTONDOWN:
                        if controller.get_button(3):  # Triangle
                            player1.rotate()
                        elif controller.get_button(0):  # X
                            player1.hard_drop()
            
            # Handle continuous movement
            player1.handle_continuous_movement(current_time, move_delay)
            player2.handle_continuous_movement(current_time, move_delay)
            
            # Update game state
            player1.update(current_time)
            player2.update(current_time)
            
            # Draw everything
            screen.fill(GRAY)
            
            # Title
            title_text = font_big.render("MULTIPLAYER TETRIS", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            screen.blit(title_text, title_rect)
            
            # Calculate grid positions
            grid_width = GRID_WIDTH * CELL_SIZE
            grid_height = GRID_HEIGHT * CELL_SIZE
            grid_y = 80
            
            p1_grid_x = SCREEN_WIDTH // 4 - grid_width // 2
            p2_grid_x = 3 * SCREEN_WIDTH // 4 - grid_width // 2
            
            # Draw grids
            player1.grid.draw(screen, p1_grid_x, grid_y)
            player2.grid.draw(screen, p2_grid_x, grid_y)
            
            # Draw current pieces
            if player1.current_block and player1.active:
                player1.current_block.draw(screen, p1_grid_x, grid_y)
            
            if player2.current_block and player2.active:
                player2.current_block.draw(screen, p2_grid_x, grid_y)
            
            # Draw divider
            pygame.draw.line(screen, WHITE, 
                           (SCREEN_WIDTH // 2, 60), 
                           (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60), 2)
            
            # Draw player labels
            p1_label = font_medium.render("PLAYER 1", True, WHITE)
            screen.blit(p1_label, (p1_grid_x, grid_y - 30))
            
            p2_label = font_medium.render("PLAYER 2", True, WHITE)
            screen.blit(p2_label, (p2_grid_x, grid_y - 30))
            
            # Draw status
            if not player1.active:
                p1_status = font_medium.render("GAME OVER", True, RED)
                screen.blit(p1_status, (p1_grid_x, grid_y - 55))
            
            if not player2.active:
                p2_status = font_medium.render("GAME OVER", True, RED)
                screen.blit(p2_status, (p2_grid_x, grid_y - 55))
            
            # Draw info
            info_y = grid_y + grid_height + 10
            
            # Player 1 info
            p1_score = font_small.render(f"Score: {player1.score:,}", True, WHITE)
            screen.blit(p1_score, (p1_grid_x, info_y))
            
            p1_lines = font_small.render(f"Lines: {player1.lines_cleared}", True, WHITE)
            screen.blit(p1_lines, (p1_grid_x, info_y + 25))
            
            p1_controls = font_small.render("← → ↓ ↑ RShift", True, (200, 200, 200))
            screen.blit(p1_controls, (p1_grid_x, info_y + 50))
            
            # Player 2 info
            p2_score = font_small.render(f"Score: {player2.score:,}", True, WHITE)
            screen.blit(p2_score, (p2_grid_x, info_y))
            
            p2_lines = font_small.render(f"Lines: {player2.lines_cleared}", True, WHITE)
            screen.blit(p2_lines, (p2_grid_x, info_y + 25))
            
            p2_controls = font_small.render("A D S W Space", True, (200, 200, 200))
            screen.blit(p2_controls, (p2_grid_x, info_y + 50))
            
            # Draw timer
            remaining_seconds = remaining_time // 1000
            timer_text = font_medium.render(f"Time: {remaining_seconds}s", True, WHITE)
            timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            screen.blit(timer_text, timer_rect)
            
            pygame.display.flip()
            clock.tick(60)
        
        # Determine winner
        stop_music()
        
        if player1.score > player2.score:
            winner = "Player 1"
        elif player2.score > player1.score:
            winner = "Player 2"
        else:
            winner = "tie"
        
        # Show end screen
        play_again = show_end_screen(screen, winner, player1.score, player2.score)
        
        if play_again:
            # Restart music for next game
            play_music(volume=0.5)