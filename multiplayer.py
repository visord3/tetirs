# multiplayer.py - completely rewritten version
import sys
import pygame
import random
import os

# Import from the single_player module
from single_player import COLORS, SHAPES, CELL_SIZE, LEVEL_SPEED

# Import sound manager
from sound_manager import load_game_sounds, play_sound, play_music, stop_music, ensure_music_playing


#########################
# Helper functions
#########################
def spawn_block(grid_width):
    """Generate a new Tetris piece for multiplayer"""
    shape_idx = random.randint(0, len(SHAPES) - 1)
    shape = [row[:] for row in SHAPES[shape_idx]]
    color = COLORS[shape_idx]
    
    # Use the exact same approach as single player for initial positioning
    x = grid_width // 2 - len(shape[0]) // 2
    # Important: Start at position 0 to ensure correct spawning
    y = 0
    
    return Block(shape, color, x, y)


def adjust_fall_speed(lines):
    """Adjust fall speed based on lines cleared"""
    level = min(10, lines // 10 + 1)
    return LEVEL_SPEED[min(9, level - 1)]


def get_line_clear_score(lines, level=1):
    """Calculate score for lines cleared"""
    return lines * lines * 100 * level


#########################
# Block class for multiplayer
#########################
class Block:
    def __init__(self, shape, color, col_offset=0, row_offset=0):
        self.shape = shape
        self.color = color
        self.col_offset = col_offset
        self.row_offset = row_offset
        self.height = len(shape)
        self.width = len(shape[0])

    def draw(self, screen, offset_x=0, offset_y=0):
        for row_idx, row in enumerate(self.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        screen,
                        self.color,
                        (
                            offset_x + (self.col_offset + col_idx) * CELL_SIZE,
                            offset_y + (self.row_offset + row_idx) * CELL_SIZE,
                            CELL_SIZE - 1,
                            CELL_SIZE - 1
                        )
                    )

    def rotate(self, grid):
        # Save the original shape for reverting if needed
        original_shape = [row[:] for row in self.shape]
        original_width = self.width
        original_height = self.height

        # Perform rotation (transpose and reverse rows for clockwise)
        rotated = list(zip(*self.shape[::-1]))
        self.shape = [list(row) for row in rotated]
        self.height = len(self.shape)
        self.width = len(self.shape[0])

        # Check if rotation is valid
        if not self.is_valid_position(grid):
            # Restore original shape if collision occurred
            self.shape = original_shape
            self.width = original_width
            self.height = original_height
            return False
        return True

    def move(self, drow, dcol, grid):
        """
        Attempt to move the block. Return True if successful, False otherwise.
        """
        original_row = self.row_offset
        original_col = self.col_offset
        
        # Try to move
        self.row_offset += drow
        self.col_offset += dcol
        
        # Check if new position is valid
        if not self.is_valid_position(grid):
            # Revert if invalid
            self.row_offset = original_row
            self.col_offset = original_col
            return False
        
        return True

    def is_valid_position(self, grid):
        """Check if current position is valid (not colliding, in bounds)"""
        for row_idx, row in enumerate(self.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    grid_row = self.row_offset + row_idx
                    grid_col = self.col_offset + col_idx
                    
                    # Check boundaries - explicitly ensure blocks are within horizontal boundaries
                    if grid_col < 0 or grid_col >= grid.width:
                        return False
                    
                    # Check bottom boundary - this is crucial for proper locking
                    if grid_row >= grid.height:
                        return False
                    
                    # Check collision with existing blocks, but only if we're within the grid
                    # This check allows blocks to come in from the top
                    if grid_row >= 0 and grid.grid[grid_row][grid_col] != 0:
                        return False
        
        return True


#########################
# Grid class for multiplayer
#########################
class Grid:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

    def draw(self, screen, offset_x=0, offset_y=0):
        # Draw grid background
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (offset_x, offset_y, self.width * self.cell_size, self.height * self.cell_size)
        )

        # Draw grid cells
        for row in range(self.height):
            for col in range(self.width):
                cell_value = self.grid[row][col]
                if cell_value != 0:  # Not an empty cell
                    pygame.draw.rect(
                        screen,
                        cell_value,  # Color stored in grid
                        (
                            offset_x + col * self.cell_size,
                            offset_y + row * self.cell_size,
                            self.cell_size - 1,
                            self.cell_size - 1
                        )
                    )

        # Draw grid outline
        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (offset_x, offset_y, self.width * self.cell_size, self.height * self.cell_size),
            2
        )

    def place_block(self, block):
        """Lock the block's cells into the grid"""
        cells_placed = 0
        
        for row_idx, row in enumerate(block.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    grid_row = block.row_offset + row_idx
                    grid_col = block.col_offset + col_idx
                    
                    # Make sure we're in bounds
                    if 0 <= grid_row < self.height and 0 <= grid_col < self.width:
                        self.grid[grid_row][grid_col] = block.color
                        cells_placed += 1
        
        # Debug info
        if cells_placed > 0:
            print(f"Block placed at row={block.row_offset}, col={block.col_offset}. Cells placed: {cells_placed}")
        else:
            print("WARNING: No cells were placed! Possible collision detection issue.")
            
        return cells_placed

    def clear_rows(self):
        """Clear completed rows and return the number cleared"""
        rows_cleared = 0
        row = self.height - 1
        
        while row >= 0:
            # Check if this row is full (no zeros)
            if all(cell != 0 for cell in self.grid[row]):
                # Move all rows above down by one
                for move_row in range(row, 0, -1):
                    self.grid[move_row] = self.grid[move_row - 1][:]
                
                # Clear the top row
                self.grid[0] = [0 for _ in range(self.width)]
                rows_cleared += 1
            else:
                # Only move to the next row if we didn't clear the current one
                row -= 1
                
        return rows_cleared


#########################
# Player class to manage each player's state
#########################
class Player:
    def __init__(self, grid_width, grid_height):
        self.grid = Grid(grid_width, grid_height, CELL_SIZE)
        self.current_block = spawn_block(grid_width)
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.active = True
        self.fall_speed = LEVEL_SPEED[0]  # Start with level 1 speed
        self.last_drop_time = pygame.time.get_ticks()
        self.last_move_time = pygame.time.get_ticks()
        
        # Input state
        self.left_pressed = False
        self.right_pressed = False
        self.down_pressed = False
        
        # Validate initial block position
        if not self.current_block.is_valid_position(self.grid):
            print("WARNING: Initial block position is invalid!")

    def update(self, current_time):
        """Update the player's game state"""
        if not self.active:
            return
            
        # Handle automatic piece drop
        if current_time - self.last_drop_time >= self.fall_speed:
            self.drop_block()
            self.last_drop_time = current_time
            
    def drop_block(self):
        """Move block down one step, handle locking if needed"""
        if not self.active or not self.current_block:
            return False
            
        # Try to move down - use the move method for consistency
        if not self.current_block.move(1, 0, self.grid):
            # Block couldn't move down, so lock it and spawn a new one
            success = self.lock_block()
            
            # Debugging info
            if not success:
                print("WARNING: Failed to lock block!")
                
            return False
        return True
            
    def lock_block(self):
        """Lock block in place, clear rows, spawn new block"""
        if not self.current_block:
            return False
            
        # Place the block on the grid
        cells_placed = self.grid.place_block(self.current_block)
        if cells_placed > 0:
            play_sound("drop")
            
            # Clear completed rows
            rows_cleared = self.grid.clear_rows()
            if rows_cleared > 0:
                play_sound("clear")
                self.lines_cleared += rows_cleared
                self.level = min(10, self.lines_cleared // 10 + 1)
                self.score += rows_cleared * rows_cleared * 100 * self.level
                self.fall_speed = adjust_fall_speed(self.lines_cleared)
                
            # Spawn a new block
            self.current_block = spawn_block(self.grid.width)
            
            # Check if new block can be placed (GAME OVER check)
            if not self.current_block.is_valid_position(self.grid):
                print("Game over - new block cannot be placed")
                self.active = False
                self.current_block = None
                play_sound("game_over")
                
            return True
        else:
            print("WARNING: Failed to place block on grid!")
            return False

    def hard_drop(self):
        """Drop the block to the bottom immediately"""
        if not self.active or not self.current_block:
            return
            
        # Keep moving down until hitting something
        drop_count = 0
        while self.current_block.move(1, 0, self.grid):
            drop_count += 1
            
        if drop_count > 0:
            print(f"Hard drop moved block down {drop_count} cells")
        else:
            print("Hard drop didn't move the block at all - collision detected")
            
        # Lock the block
        self.lock_block()

    def handle_continuous_movement(self, current_time, move_delay):
        """Handle continuous movement when keys are held down"""
        if not self.active or not self.current_block:
            return
            
        if current_time - self.last_move_time <= move_delay:
            return
            
        if self.left_pressed:
            if self.current_block.move(0, -1, self.grid):
                self.last_move_time = current_time
        elif self.right_pressed:
            if self.current_block.move(0, 1, self.grid):
                self.last_move_time = current_time
        elif self.down_pressed:
            if not self.drop_block():
                # Block was locked, no need to set last_move_time
                pass
            else:
                self.last_move_time = current_time


#########################
# END SCREEN
#########################
def show_end_screen(screen, winner, width, height):
    """
    Displays an end screen indicating the winner (or tie),
    and offers "Play Again" or "Quit".
    Returns True if "Play Again" is clicked, otherwise exits.
    """
    font = pygame.font.SysFont("Arial", 36)
    running = True

    # Initialize controller if available
    controller = None
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
        print(f"Controller connected: {controller.get_name()}")

    selected_option = 0  # 0 = Play Again, 1 = Quit
    button_cooldown = 0
    cooldown_time = 200  # milliseconds
    clock = pygame.time.Clock()
    
    # Button dimensions
    button_width = 300
    button_height = 50
    button_spacing = 30
    
    # Stop the in-game music and play game over sound
    stop_music()
    play_sound("game_over")

    while running:
        dt = clock.tick(60)
        if button_cooldown > 0:
            button_cooldown -= dt

        # Fill screen with semi-transparent black overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Display winner text
        if winner == "tie":
            end_text = font.render("It's a tie!", True, (255, 255, 255))
        else:
            end_text = font.render(f"{winner} Wins!", True, (255, 255, 255))
        end_rect = end_text.get_rect(center=(width // 2, height // 2 - 80))
        screen.blit(end_text, end_rect)
        
        # Calculate centered positions for buttons
        play_again_y = height // 2 + 20
        quit_y = height // 2 + 20 + button_height + button_spacing
        button_x = width // 2 - button_width // 2

        # Play Again button
        play_again_button = pygame.Rect(button_x, play_again_y, button_width, button_height)
        play_again_color = (100, 100, 255) if selected_option == 0 else (255, 255, 255)
        pygame.draw.rect(screen, play_again_color, play_again_button)
        play_again_text = font.render("Play Again", True, (0, 0, 0))
        play_again_rect = play_again_text.get_rect(center=play_again_button.center)
        screen.blit(play_again_text, play_again_rect)

        # Quit button
        quit_button = pygame.Rect(button_x, quit_y, button_width, button_height)
        quit_color = (100, 100, 255) if selected_option == 1 else (255, 255, 255)
        pygame.draw.rect(screen, quit_color, quit_button)
        quit_text = font.render("Quit", True, (0, 0, 0))
        quit_rect = quit_text.get_rect(center=quit_button.center)
        screen.blit(quit_text, quit_rect)
        
        # Draw a decorative winner trophy or tie icon
        if winner != "tie":
            trophy_text = "🏆"
            trophy_font = pygame.font.SysFont("Arial", 64)
            trophy_render = trophy_font.render(trophy_text, True, (255, 215, 0))  # Gold color
            trophy_rect = trophy_render.get_rect(center=(width // 2, height // 2 - 150))
            screen.blit(trophy_render, trophy_rect)
        else:
            tie_text = "🤝"
            tie_font = pygame.font.SysFont("Arial", 64)
            tie_render = tie_font.render(tie_text, True, (255, 255, 255))
            tie_rect = tie_render.get_rect(center=(width // 2, height // 2 - 150))
            screen.blit(tie_render, tie_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Keyboard controls
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                    selected_option = 1 - selected_option  # Toggle between 0 and 1
                    play_sound("rotate")  # Add sound feedback for menu navigation
                    button_cooldown = cooldown_time
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected_option == 0:
                        return True  # "Play Again"
                    else:
                        pygame.quit()
                        sys.exit()

            # Mouse controls
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_button.collidepoint(event.pos):
                    return True  # "Play Again"
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            # Controller controls
            if controller:
                # D-pad navigation
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = controller.get_hat(0)
                    if hat_y != 0 and button_cooldown <= 0:
                        selected_option = 1 - selected_option  # Toggle between 0 and 1
                        play_sound("rotate")  # Add sound feedback for menu navigation
                        button_cooldown = cooldown_time

                # Analog stick navigation
                if event.type == pygame.JOYAXISMOTION:
                    left_stick_y = controller.get_axis(1)
                    deadzone = 0.5

                    if abs(left_stick_y) > deadzone and button_cooldown <= 0:
                        selected_option = 1 if left_stick_y > 0 else 0
                        play_sound("rotate")  # Add sound feedback for menu navigation
                        button_cooldown = cooldown_time

                # X button (0) or Circle button (1) to select
                if event.type == pygame.JOYBUTTONDOWN:
                    if controller.get_button(0) or controller.get_button(1):
                        if selected_option == 0:
                            return True  # "Play Again"
                        else:
                            pygame.quit()
                            sys.exit()

        pygame.display.flip()

    return False


#########################
# MULTIPLAYER MODE - main function
#########################
def multiplayer_mode():
    # Constants
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    GRID_WIDTH = 10
    GRID_HEIGHT = 20

    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multiplayer Tetris")

    # Initialize controller if available
    controller = None
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
        print(f"Controller connected: {controller.get_name()}")

    # Initialize sounds with higher volume to ensure music is heard
    load_game_sounds()
    play_music(volume=0.8)  # Increased volume for better audibility

    clock = pygame.time.Clock()
    running = True

    # Create two player instances
    player1 = Player(GRID_WIDTH, GRID_HEIGHT)
    player2 = Player(GRID_WIDTH, GRID_HEIGHT)

    # Game duration in seconds
    timer = 120  # 2 minutes
    start_ticks = pygame.time.get_ticks()

    # Input state and timing
    move_delay = 100  # ms between continuous movement updates

    # Font for game info
    font = pygame.font.SysFont("Arial", 24)
    title_font = pygame.font.SysFont("Arial", 36)

    # Make sure music is playing
    if not pygame.mixer.music.get_busy():
        print("Starting music...")
        play_music(volume=0.8)

    while running:
        # Check if music should be playing
        ensure_music_playing()
            
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_ticks) // 1000
        remaining_time = max(0, timer - elapsed_time)

        # Check if game is over
        if remaining_time <= 0 or (not player1.active and not player2.active):
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                stop_music()
                pygame.quit()
                sys.exit()

            # ESC to return to main menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                stop_music()
                return

            ###############
            # Keyboard Controls
            ###############
            if event.type == pygame.KEYDOWN:
                # Volume controls
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Increase volume
                    current_volume = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(min(1.0, current_volume + 0.1))
                    print(f"Volume increased to {pygame.mixer.music.get_volume():.1f}")
                elif event.key == pygame.K_MINUS or event.key == pygame.K_UNDERSCORE:
                    # Decrease volume
                    current_volume = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(max(0.0, current_volume - 0.1))
                    print(f"Volume decreased to {pygame.mixer.music.get_volume():.1f}")
                elif event.key == pygame.K_m:
                    # Toggle mute
                    if pygame.mixer.music.get_volume() > 0:
                        pygame.mixer.music.set_volume(0.0)
                        print("Music muted")
                    else:
                        pygame.mixer.music.set_volume(0.8)
                        print("Music unmuted")
                        
                # Player 1 Controls (only if active)
                if player1.active and player1.current_block:
                    if event.key == pygame.K_LEFT:
                        player1.left_pressed = True
                        player1.right_pressed = False
                        player1.current_block.move(0, -1, player1.grid)
                        player1.last_move_time = current_time
                    elif event.key == pygame.K_RIGHT:
                        player1.left_pressed = False
                        player1.right_pressed = True
                        player1.current_block.move(0, 1, player1.grid)
                        player1.last_move_time = current_time
                    elif event.key == pygame.K_DOWN:
                        player1.down_pressed = True
                        player1.drop_block()
                        player1.last_move_time = current_time
                    elif event.key == pygame.K_UP:
                        if player1.current_block.rotate(player1.grid):
                            play_sound("rotate")
                    elif event.key == pygame.K_SPACE:  # Hard drop for P1
                        player1.hard_drop()

                # Player 2 Controls (only if active)
                if player2.active and player2.current_block:
                    if event.key == pygame.K_a:
                        player2.left_pressed = True
                        player2.right_pressed = False
                        player2.current_block.move(0, -1, player2.grid)
                        player2.last_move_time = current_time
                    elif event.key == pygame.K_d:
                        player2.left_pressed = False
                        player2.right_pressed = True
                        player2.current_block.move(0, 1, player2.grid)
                        player2.last_move_time = current_time
                    elif event.key == pygame.K_s:
                        player2.down_pressed = True
                        player2.drop_block()
                        player2.last_move_time = current_time
                    elif event.key == pygame.K_w:
                        if player2.current_block.rotate(player2.grid):
                            play_sound("rotate")
                    elif event.key == pygame.K_f:  # Hard drop for P2
                        player2.hard_drop()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    player1.left_pressed = False
                elif event.key == pygame.K_RIGHT:
                    player1.right_pressed = False
                elif event.key == pygame.K_DOWN:
                    player1.down_pressed = False
                elif event.key == pygame.K_a:
                    player2.left_pressed = False
                elif event.key == pygame.K_d:
                    player2.right_pressed = False
                elif event.key == pygame.K_s:
                    player2.down_pressed = False

            ###############
            # Controller Controls (only for Player 1)
            ###############
            if controller and player1.active and player1.current_block:
                # D-pad for Player 1
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = controller.get_hat(0)

                    player1.left_pressed = (hat_x == -1)
                    player1.right_pressed = (hat_x == 1)
                    player1.down_pressed = (hat_y == -1)

                    if hat_x == -1:
                        player1.current_block.move(0, -1, player1.grid)
                        player1.last_move_time = current_time
                    elif hat_x == 1:
                        player1.current_block.move(0, 1, player1.grid)
                        player1.last_move_time = current_time
                    if hat_y == -1:
                        player1.drop_block()
                        player1.last_move_time = current_time

                # Analog stick for Player 1
                if event.type == pygame.JOYAXISMOTION:
                    left_stick_x = controller.get_axis(0)
                    left_stick_y = controller.get_axis(1)
                    deadzone = 0.5

                    # X-axis (left/right)
                    if left_stick_x < -deadzone:
                        if not player1.left_pressed:
                            player1.left_pressed = True
                            player1.right_pressed = False
                            player1.current_block.move(0, -1, player1.grid)
                            player1.last_move_time = current_time
                    elif left_stick_x > deadzone:
                        if not player1.right_pressed:
                            player1.left_pressed = False
                            player1.right_pressed = True
                            player1.current_block.move(0, 1, player1.grid)
                            player1.last_move_time = current_time
                    else:
                        player1.left_pressed = False
                        player1.right_pressed = False

                    # Y-axis (down)
                    if left_stick_y > deadzone:
                        if not player1.down_pressed:
                            player1.down_pressed = True
                            player1.drop_block()
                            player1.last_move_time = current_time
                    else:
                        player1.down_pressed = False

                # Button presses for Player 1
                if event.type == pygame.JOYBUTTONDOWN:
                    # Triangle (3) to rotate
                    if controller.get_button(3):
                        if player1.current_block.rotate(player1.grid):
                            play_sound("rotate")

                    # X button (0) for hard drop
                    elif controller.get_button(0):
                        player1.hard_drop()

        # Handle continuous movement when keys are held
        player1.handle_continuous_movement(current_time, move_delay)
        player2.handle_continuous_movement(current_time, move_delay)

        # Update game state
        player1.update(current_time)
        player2.update(current_time)

        #########################
        # DRAWING
        #########################
        screen.fill((50, 50, 50))  # Dark gray background

        # Draw title
        title_text = title_font.render("MULTIPLAYER TETRIS", True, (255, 255, 100))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
        screen.blit(title_text, title_rect)

        # Calculate grid offsets
        grid_width = player1.grid.width * CELL_SIZE
        grid_height = player1.grid.height * CELL_SIZE
        p1_offset_x = (SCREEN_WIDTH // 2 - grid_width) // 2
        p2_offset_x = SCREEN_WIDTH // 2 + (SCREEN_WIDTH // 2 - grid_width) // 2
        grid_offset_y = 70  # Leave space for title and scores

        # Draw each grid
        player1.grid.draw(screen, offset_x=p1_offset_x, offset_y=grid_offset_y)
        player2.grid.draw(screen, offset_x=p2_offset_x, offset_y=grid_offset_y)

        # Draw the vertical dividing line in the middle
        pygame.draw.line(
            screen,
            (255, 255, 255),  # white
            (SCREEN_WIDTH // 2, 0),  # start at top center
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT),  # down to bottom center
            2  # line thickness
        )

        # Draw blocks (only if player is active)
        if player1.active and player1.current_block:
            player1.current_block.draw(screen, offset_x=p1_offset_x, offset_y=grid_offset_y)
        if player2.active and player2.current_block:
            player2.current_block.draw(screen, offset_x=p2_offset_x, offset_y=grid_offset_y)

        # Draw player labels and scores
        p1_label = font.render("PLAYER 1", True, (255, 255, 255))
        p2_label = font.render("PLAYER 2", True, (255, 255, 255))
        screen.blit(p1_label, (p1_offset_x, grid_offset_y - 30))
        screen.blit(p2_label, (p2_offset_x, grid_offset_y - 30))

        # Draw player status
        if not player1.active:
            p1_status = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(p1_status, (p1_offset_x, grid_offset_y - 60))
        if not player2.active:
            p2_status = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(p2_status, (p2_offset_x, grid_offset_y - 60))

        # Scores
        score_text_p1 = font.render(f"Score: {player1.score}", True, (255, 255, 255))
        score_text_p2 = font.render(f"Score: {player2.score}", True, (255, 255, 255))
        level_text_p1 = font.render(f"Level: {player1.level}", True, (255, 255, 255))
        level_text_p2 = font.render(f"Level: {player2.level}", True, (255, 255, 255))
        lines_text_p1 = font.render(f"Lines: {player1.lines_cleared}", True, (255, 255, 255))
        lines_text_p2 = font.render(f"Lines: {player2.lines_cleared}", True, (255, 255, 255))

        # Position score info
        screen.blit(score_text_p1, (p1_offset_x, grid_offset_y + grid_height + 10))
        screen.blit(score_text_p2, (p2_offset_x, grid_offset_y + grid_height + 10))
        screen.blit(level_text_p1, (p1_offset_x, grid_offset_y + grid_height + 40))
        screen.blit(level_text_p2, (p2_offset_x, grid_offset_y + grid_height + 40))
        screen.blit(lines_text_p1, (p1_offset_x, grid_offset_y + grid_height + 70))
        screen.blit(lines_text_p2, (p2_offset_x, grid_offset_y + grid_height + 70))

        # Draw timer
        timer_text = font.render(f"Time: {remaining_time}", True, (255, 255, 255))
        timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(timer_text, timer_rect)

        # Draw controls info
        p1_controls = font.render("← → ↓ ↑ Space", True, (200, 200, 200))
        p2_controls = font.render("A D S W F", True, (200, 200, 200))
        screen.blit(p1_controls, (p1_offset_x, grid_offset_y + grid_height + 100))
        screen.blit(p2_controls, (p2_offset_x, grid_offset_y + grid_height + 100))

        # Draw volume controls info
        volume_controls = font.render("Volume: +/- (M to mute)", True, (200, 200, 200))
        screen.blit(volume_controls, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 60))

        pygame.display.flip()
        clock.tick(60)

    # Determine winner
    stop_music()
    
    if not player1.active and not player2.active:
        # Both players are out - compare scores
        if player1.score > player2.score:
            winner = "Player 1"
        elif player2.score > player1.score:
            winner = "Player 2"
        else:
            winner = "tie"
    elif not player1.active:
        # Player 1 is out
        winner = "Player 2"
    elif not player2.active:
        # Player 2 is out
        winner = "Player 1"
    else:
        # Time ran out - compare scores
        if player1.score > player2.score:
            winner = "Player 1"
        elif player2.score > player1.score:
            winner = "Player 2"
        else:
            winner = "tie"

    # Show end screen and handle replay
    if show_end_screen(screen, winner, SCREEN_WIDTH, SCREEN_HEIGHT):
        multiplayer_mode()  # Restart the mode if "Play Again" clicked