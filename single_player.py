# This file contains changes needed for single_player.py to use the same sound system
# as multiplayer.py

import pygame
import random
import sys

# Import sound management system
from sound_manager import load_game_sounds, play_sound, play_music, stop_music, ensure_music_playing

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Tetromino shapes and colors
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]]  # L
]

COLORS = [CYAN, YELLOW, MAGENTA, GREEN, RED, BLUE, ORANGE]

def get_random_block(cell_size):
    """Generate a random tetromino shape"""
    shape_index = random.randint(0, len(SHAPES) - 1)
    return SHAPES[shape_index]

# Game settings
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PREVIEW_SIZE = 4
LEVEL_SPEED = [1000, 800, 600, 500, 400, 300, 250, 200, 150, 100]  # ms per drop

# Layout constants
PANEL_WIDTH = 220
PANEL_MARGIN = 30
OUTER_MARGIN = 40
INFO_PADDING = 20
NEXT_BOX_SIZE = 4 * CELL_SIZE + 2 * INFO_PADDING
PANEL_HEIGHT = max(GRID_HEIGHT * CELL_SIZE, 350)

class SinglePlayerGame:
    def __init__(self, controller=None):
        """Initialize the single player Tetris game with optional controller support"""
        # Always initialize joystick
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
        else:
            self.controller = None

        # Game state
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.next_piece = None
        self.piece_x = 0
        self.piece_y = 0
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        
        # Timer for tracking gameplay time
        self.start_time = pygame.time.get_ticks()
        self.total_time = 0  # In milliseconds
        self.paused_time = 0  # To track time while paused

        # Timing
        self.clock = pygame.time.Clock()
        self.drop_time = pygame.time.get_ticks()
        self.move_time = pygame.time.get_ticks()
        self.speed = LEVEL_SPEED[0]
        self.move_delay = 100  # ms between moves when holding a direction

        # Input state for both keyboard and controller
        self.left_pressed = False
        self.right_pressed = False
        self.down_pressed = False

        # Initialize sounds
        load_game_sounds()

        # Fonts
        self.font_big = pygame.font.SysFont("Arial", 36)
        self.font_medium = pygame.font.SysFont("Arial", 24)
        self.font_small = pygame.font.SysFont("Arial", 18)

        # Start the game
        self.new_piece()
        self.new_piece()  # This creates both current and next piece

    def new_piece(self):
        """Generate a new Tetris piece"""
        if self.next_piece:
            self.current_piece = self.next_piece
            self.color_index = self.next_color_index
        else:
            self.color_index = random.randint(0, len(SHAPES) - 1)
            self.current_piece = [row[:] for row in SHAPES[self.color_index]]

        self.next_color_index = random.randint(0, len(SHAPES) - 1)
        self.next_piece = [row[:] for row in SHAPES[self.next_color_index]]

        # Starting position
        self.piece_x = GRID_WIDTH // 2 - len(self.current_piece[0]) // 2
        self.piece_y = 0

        # Check if new piece overlaps with existing blocks (game over)
        if self.check_collision():
            self.game_over = True
            play_sound("game_over")

    def rotate_piece(self):
        """Rotate the current piece clockwise"""
        # Save original piece to restore if rotation is not possible
        original_piece = [row[:] for row in self.current_piece]

        # Perform rotation (transpose and reverse rows)
        # Convert to list to handle irregular shapes
        rotated = list(zip(*self.current_piece[::-1]))
        self.current_piece = [list(row) for row in rotated]

        # Check if rotation is valid
        if self.check_collision():
            # Restore original piece if rotation causes collision
            self.current_piece = original_piece
            return False
        
        # Play rotation sound
        play_sound("rotate")
        return True

    def check_collision(self):
        """Check if current piece collides with borders or other pieces"""
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell:
                    # Check if piece is outside grid boundaries
                    grid_x = self.piece_x + x
                    grid_y = self.piece_y + y

                    if (grid_x < 0 or grid_x >= GRID_WIDTH or
                            grid_y >= GRID_HEIGHT or
                            (grid_y >= 0 and self.grid[grid_y][grid_x])):
                        return True
        return False

    def merge_piece(self):
        """Merge current piece with the grid"""
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell and 0 <= self.piece_y + y < GRID_HEIGHT:
                    self.grid[self.piece_y + y][self.piece_x + x] = self.color_index + 1
        
        # Play drop sound
        play_sound("drop")

    def clear_lines(self):
        """Clear completed lines and return number of lines cleared"""
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                # Move all lines above down
                for move_y in range(y, 0, -1):
                    self.grid[move_y] = self.grid[move_y - 1][:]
                # Clear the top line
                self.grid[0] = [0] * GRID_WIDTH
                lines_cleared += 1
            else:
                y -= 1

        # Update score and level
        if lines_cleared > 0:
            play_sound("clear")
            self.score += lines_cleared * lines_cleared * 100 * self.level
            self.lines_cleared += lines_cleared
            old_level = self.level
            self.level = min(10, self.lines_cleared // 10 + 1)
            if self.level > old_level:
                play_sound("level_up")
            self.speed = LEVEL_SPEED[min(9, self.level - 1)]

        return lines_cleared

    def move_left(self):
        """Move the piece left if possible"""
        self.piece_x -= 1
        if self.check_collision():
            self.piece_x += 1
            return False
        play_sound("move")
        return True

    def move_right(self):
        """Move the piece right if possible"""
        self.piece_x += 1
        if self.check_collision():
            self.piece_x -= 1
            return False
        play_sound("move")
        return True

    def move_down(self):
        """Move the piece down if possible"""
        self.piece_y += 1
        if self.check_collision():
            self.piece_y -= 1
            # Piece can't move down further, place it
            self.merge_piece()
            self.clear_lines()
            self.new_piece()
            return False
        return True

    def drop_piece(self):
        """Hard drop the piece to the bottom"""
        while self.move_down():
            pass
        play_sound("drop")

    def update(self):
        """Update game state"""
        if self.game_over or self.paused:
            return

        current_time = pygame.time.get_ticks()
        
        # Update game timer
        if not self.game_over and not self.paused:
            self.total_time = current_time - self.start_time

        # Handle automatic piece drop
        if current_time - self.drop_time > self.speed:
            self.move_down()
            self.drop_time = current_time

        # Handle continuous movement when a direction is held
        if current_time - self.move_time > self.move_delay:
            if self.left_pressed:
                self.move_left()
                self.move_time = current_time
            elif self.right_pressed:
                self.move_right()
                self.move_time = current_time
            elif self.down_pressed:
                self.move_down()
                self.move_time = current_time

    def handle_input(self, event):
        """Handle keyboard and controller input"""
        # Keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.left_pressed = True
                self.move_left()
                self.move_time = pygame.time.get_ticks()
            elif event.key == pygame.K_RIGHT:
                self.right_pressed = True
                self.move_right()
                self.move_time = pygame.time.get_ticks()
            elif event.key == pygame.K_DOWN:
                self.down_pressed = True
                self.move_down()
                self.move_time = pygame.time.get_ticks()
            elif event.key == pygame.K_UP:
                self.rotate_piece()
            elif event.key == pygame.K_SPACE:
                self.drop_piece()
            elif event.key == pygame.K_p:
                # Toggle pause state and handle timer accordingly
                if not self.paused:
                    # Pause the game - record the time when paused
                    self.paused = True
                    self.paused_time = pygame.time.get_ticks()
                else:
                    # Unpause the game - adjust the start time
                    self.paused = False
                    # Add the paused duration to the start time
                    pause_duration = pygame.time.get_ticks() - self.paused_time
                    self.start_time += pause_duration
            elif event.key == pygame.K_r and self.game_over:
                self.__init__(self.controller)  # Reset game
                play_music()  # Restart music
            # Volume controls
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                current_volume = pygame.mixer.music.get_volume()
                pygame.mixer.music.set_volume(min(1.0, current_volume + 0.1))
            elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                current_volume = pygame.mixer.music.get_volume()
                pygame.mixer.music.set_volume(max(0.0, current_volume - 0.1))
            elif event.key == pygame.K_m:
                if pygame.mixer.music.get_volume() > 0:
                    pygame.mixer.music.set_volume(0.0)
                else:
                    pygame.mixer.music.set_volume(0.7)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.left_pressed = False
            elif event.key == pygame.K_RIGHT:
                self.right_pressed = False
            elif event.key == pygame.K_DOWN:
                self.down_pressed = False

        # Controller events (if controller is connected)
        if self.controller:
            # D-pad movement
            if event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = self.controller.get_hat(0)

                self.left_pressed = (hat_x == -1)
                self.right_pressed = (hat_x == 1)
                self.down_pressed = (hat_y == -1)

                if hat_x == -1:
                    self.move_left()
                    self.move_time = pygame.time.get_ticks()
                elif hat_x == 1:
                    self.move_right()
                    self.move_time = pygame.time.get_ticks()
                if hat_y == -1:
                    self.move_down()
                    self.move_time = pygame.time.get_ticks()

            # Analog stick movement
            if event.type == pygame.JOYAXISMOTION:
                # Left analog stick
                left_stick_x = self.controller.get_axis(0)
                left_stick_y = self.controller.get_axis(1)
                deadzone = 0.5

                # X-axis (left/right)
                if left_stick_x < -deadzone:
                    if not self.left_pressed:
                        self.left_pressed = True
                        self.right_pressed = False
                        self.move_left()
                        self.move_time = pygame.time.get_ticks()
                elif left_stick_x > deadzone:
                    if not self.right_pressed:
                        self.left_pressed = False
                        self.right_pressed = True
                        self.move_right()
                        self.move_time = pygame.time.get_ticks()
                else:
                    self.left_pressed = False
                    self.right_pressed = False

                # Y-axis (down)
                if left_stick_y > deadzone:
                    if not self.down_pressed:
                        self.down_pressed = True
                        self.move_down()
                        self.move_time = pygame.time.get_ticks()
                else:
                    self.down_pressed = False

            # Button presses
            if event.type == pygame.JOYBUTTONDOWN:
                # Triangle (3) for rotate
                if self.controller.get_button(3):
                    self.rotate_piece()

                # X button (0) for hard drop
                elif self.controller.get_button(0):
                    self.drop_piece()

                # Start button (9) for pause
                elif self.controller.get_button(9):
                    self.paused = not self.paused

                # Share button (8) for restart when game over
                elif self.controller.get_button(8) and self.game_over:
                    self.__init__(self.controller)  # Reset game
                    play_music()  # Restart music

    def draw_grid(self, screen, offset_x, offset_y):
        """Draw the game grid and current piece"""
        # Draw grid background
        pygame.draw.rect(screen, BLACK, (offset_x, offset_y, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))

        # Draw grid cells
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    color_idx = self.grid[y][x] - 1
                    pygame.draw.rect(screen, COLORS[color_idx],
                                     (offset_x + x * CELL_SIZE, offset_y + y * CELL_SIZE,
                                      CELL_SIZE - 1, CELL_SIZE - 1))

        # Draw current falling piece
        if not self.game_over:
            for y, row in enumerate(self.current_piece):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(screen, COLORS[self.color_index],
                                         (offset_x + (self.piece_x + x) * CELL_SIZE,
                                          offset_y + (self.piece_y + y) * CELL_SIZE,
                                          CELL_SIZE - 1, CELL_SIZE - 1))

        # Draw grid outline
        pygame.draw.rect(screen, WHITE, (offset_x, offset_y, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE), 2)

    def draw_next_piece(self, screen, offset_x, offset_y):
        """Draw the preview of the next piece"""
        # Box for next piece preview
        pygame.draw.rect(screen, BLACK, (offset_x, offset_y, PREVIEW_SIZE * CELL_SIZE, PREVIEW_SIZE * CELL_SIZE))
        pygame.draw.rect(screen, WHITE, (offset_x, offset_y, PREVIEW_SIZE * CELL_SIZE, PREVIEW_SIZE * CELL_SIZE), 2)

        # Draw the next piece centered in the preview box
        next_width = len(self.next_piece[0])
        next_height = len(self.next_piece)
        start_x = offset_x + (PREVIEW_SIZE - next_width) * CELL_SIZE // 2
        start_y = offset_y + (PREVIEW_SIZE - next_height) * CELL_SIZE // 2

        for y, row in enumerate(self.next_piece):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, COLORS[self.next_color_index],
                                     (start_x + x * CELL_SIZE, start_y + y * CELL_SIZE,
                                      CELL_SIZE - 1, CELL_SIZE - 1))

    def draw_info(self, screen, offset_x, offset_y):
        """Draw game information"""
        # Draw score with a nice background
        score_bg = pygame.Surface((200, 150))
        score_bg.fill(GRAY)
        pygame.draw.rect(score_bg, WHITE, score_bg.get_rect(), 2)
        
        # Draw score text
        score_text = self.font_big.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(100, 30))
        score_bg.blit(score_text, score_rect)
        
        # Draw level text
        level_text = self.font_medium.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(100, 70))
        score_bg.blit(level_text, level_rect)
        
        # Convert milliseconds to minutes:seconds format
        minutes = self.total_time // 60000
        seconds = (self.total_time % 60000) // 1000
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Draw timer text
        time_text = self.font_medium.render(f"Time: {time_str}", True, WHITE)
        time_rect = time_text.get_rect(center=(100, 110))
        score_bg.blit(time_text, time_rect)
        
        # Draw the score panel
        screen.blit(score_bg, (offset_x + GRID_WIDTH * CELL_SIZE + 20, offset_y))
        
        # Draw next piece preview
        self.draw_next_piece(screen, offset_x, offset_y + 120)
        
        # Draw controls
        self.draw_controls(screen, offset_x, offset_y + 300)

    def draw_controls(self, screen, offset_x, offset_y):
        """Draw control information"""
        title_text = self.font_medium.render("Controls:", True, WHITE)
        screen.blit(title_text, (offset_x, offset_y))

        controls = []
        if self.controller:
            controls = [
                "D-Pad/Left Stick: Move",
                "Triangle: Rotate",
                "X: Hard Drop",
                "Start: Pause",
                "Share: Restart"
            ]
        else:
            controls = [
                "Arrow Keys: Move",
                "Up Arrow: Rotate",
                "Space: Hard Drop",
                "P: Pause",
                "R: Restart"
            ]

        for i, control in enumerate(controls):
            control_text = self.font_small.render(control, True, WHITE)
            screen.blit(control_text, (offset_x, offset_y + 30 + i * 20))

    def draw_game_over(self, screen, width, height):
        """Draw game over screen"""
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        game_over_text = self.font_big.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(width // 2, height // 2 - 40))
        screen.blit(game_over_text, text_rect)

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(width // 2, height // 2))
        screen.blit(score_text, score_rect)

        if self.controller:
            restart_text = self.font_medium.render("Press Share Button to Restart", True, WHITE)
        else:
            restart_text = self.font_medium.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(width // 2, height // 2 + 40))
        screen.blit(restart_text, restart_rect)

    def draw_pause(self, screen, width, height):
        """Draw pause screen"""
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        pause_text = self.font_big.render("PAUSED", True, WHITE)
        text_rect = pause_text.get_rect(center=(width // 2, height // 2))
        screen.blit(pause_text, text_rect)

        if self.controller:
            continue_text = self.font_medium.render("Press Start Button to Continue", True, WHITE)
        else:
            continue_text = self.font_medium.render("Press P to Continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(width // 2, height // 2 + 40))
        screen.blit(continue_text, continue_rect)

    def check_controller(self):
        """Check and re-initialize controller if needed"""
        if not self.controller or not self.controller.get_init():
            pygame.joystick.quit()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
            else:
                self.controller = None

    def run(self, screen):
        """Run the game loop"""
        # Calculate window size and positions
        window_width = OUTER_MARGIN * 2 + GRID_WIDTH * CELL_SIZE + PANEL_MARGIN + PANEL_WIDTH
        window_height = OUTER_MARGIN * 2 + PANEL_HEIGHT
        screen = pygame.display.set_mode((window_width, window_height))
        grid_x = OUTER_MARGIN
        grid_y = OUTER_MARGIN
        panel_x = grid_x + GRID_WIDTH * CELL_SIZE + PANEL_MARGIN
        panel_y = grid_y
        score_y = panel_y + INFO_PADDING
        next_y = score_y + 100 + INFO_PADDING
        controls_y = next_y + NEXT_BOX_SIZE + INFO_PADDING

        # Play background music
        play_music()

        # Game loop
        running = True
        while running:
            self.check_controller()  # Check for controller reconnection
            # Check if music should be playing
            ensure_music_playing()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    stop_music()
                    return

                # Listen for escape key to return to main menu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    stop_music()
                    return

                # Controller back button to return to main menu
                if self.controller and event.type == pygame.JOYBUTTONDOWN:
                    if self.controller.get_button(1):  # Circle button (1)
                        running = False
                        stop_music()
                        return

                # Handle game input
                self.handle_input(event)

            # Game logic update
            self.update()

            # Clear screen
            screen.fill(GRAY)

            # Draw volume controls info
            volume_text = self.font_small.render("Volume: +/- (M to mute)", True, WHITE)
            screen.blit(volume_text, (window_width // 2 - 100, window_height - 30))

            # Draw game elements
            self.draw_grid(screen, grid_x, grid_y)
            self.draw_info(screen, panel_x, panel_y)
            # Draw controls using the existing method
            self.draw_controls(screen, panel_x + INFO_PADDING, controls_y)

            # Draw pause or game over overlay if necessary
            if self.paused:
                self.draw_pause(screen, window_width, window_height)
            elif self.game_over:
                self.draw_game_over(screen, window_width, window_height)

            # Update the display
            pygame.display.flip()

            # Control game speed
            self.clock.tick(60)


def single_player_mode():
    """Legacy function to maintain compatibility with original code"""
    # This function just redirects to the class-based implementation
    pygame.init()
    pygame.mixer.init()

    # Initialize controller
    controller = None
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()

    # Create a window
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Tetris - Single Player")

    # Start the game
    game = SinglePlayerGame(controller)
    game.run(screen)