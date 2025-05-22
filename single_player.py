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
PANEL_HEIGHT = max(GRID_HEIGHT * CELL_SIZE, 350) # Adjusted to ensure enough space for all info

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
        self.paused_start_time = 0 # To track when pause began
        self.time_spent_paused = 0 # To track total time spent paused


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
        if self.game_over or self.paused: return False
        original_piece = [row[:] for row in self.current_piece]
        rotated = list(zip(*self.current_piece[::-1]))
        self.current_piece = [list(row) for row in rotated]

        if self.check_collision():
            self.current_piece = original_piece
            return False
        
        play_sound("rotate")
        return True

    def check_collision(self):
        """Check if current piece collides with borders or other pieces"""
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell:
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
                if cell and 0 <= self.piece_y + y < GRID_HEIGHT: # Ensure piece_y + y is within grid
                    self.grid[self.piece_y + y][self.piece_x + x] = self.color_index + 1
        play_sound("drop")

    def clear_lines(self):
        """Clear completed lines and return number of lines cleared"""
        lines_cleared_count = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                for move_y in range(y, 0, -1):
                    self.grid[move_y] = self.grid[move_y - 1][:]
                self.grid[0] = [0] * GRID_WIDTH
                lines_cleared_count += 1
            else:
                y -= 1

        if lines_cleared_count > 0:
            play_sound("clear")
            self.score += lines_cleared_count * lines_cleared_count * 100 * self.level
            self.lines_cleared += lines_cleared_count
            old_level = self.level
            self.level = min(10, self.lines_cleared // 10 + 1)
            if self.level > old_level:
                play_sound("level_up")
            self.speed = LEVEL_SPEED[min(9, self.level - 1)]
        return lines_cleared_count

    def move_left(self):
        """Move the piece left if possible"""
        if self.game_over or self.paused: return False
        self.piece_x -= 1
        if self.check_collision():
            self.piece_x += 1
            return False
        play_sound("move")
        return True

    def move_right(self):
        """Move the piece right if possible"""
        if self.game_over or self.paused: return False
        self.piece_x += 1
        if self.check_collision():
            self.piece_x -= 1
            return False
        play_sound("move")
        return True

    def move_down(self):
        """Move the piece down if possible"""
        if self.game_over or self.paused: return False
        self.piece_y += 1
        if self.check_collision():
            self.piece_y -= 1
            self.merge_piece()
            self.clear_lines()
            self.new_piece()
            return False
        return True

    def drop_piece(self):
        """Hard drop the piece to the bottom"""
        if self.game_over or self.paused: return
        while self.move_down():
            self.score +=2 # Add small score for hard drop
        # play_sound("drop") # move_down already calls merge_piece which plays drop sound

    def update(self):
        """Update game state"""
        if self.game_over or self.paused:
            if self.paused and not self.game_over: # Keep updating timer display even if paused
                 current_time = pygame.time.get_ticks()
                 self.total_time = (current_time - self.start_time) - self.time_spent_paused
            return

        current_time = pygame.time.get_ticks()
        
        if not self.game_over and not self.paused:
            self.total_time = (current_time - self.start_time) - self.time_spent_paused


        if current_time - self.drop_time > self.speed:
            self.move_down()
            self.drop_time = current_time

        if current_time - self.move_time > self.move_delay:
            if self.left_pressed:
                self.move_left()
                self.move_time = current_time
            elif self.right_pressed:
                self.move_right()
                self.move_time = current_time
            elif self.down_pressed:
                if self.move_down(): # Only add score if soft drop is successful
                    self.score +=1
                self.move_time = current_time


    def handle_input(self, event):
        """Handle keyboard and controller input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                if not self.game_over:
                    if not self.paused:
                        self.paused = True
                        self.paused_start_time = pygame.time.get_ticks() # Record when pause starts
                        stop_music() # Optionally pause music
                    else:
                        self.paused = False
                        self.time_spent_paused += pygame.time.get_ticks() - self.paused_start_time # Add duration of this pause
                        play_music() # Optionally resume music
                return # Prevent other actions if pause key is pressed
            
            if self.paused and event.key != pygame.K_p : return # Ignore other inputs if paused

            if self.game_over:
                if event.key == pygame.K_r:
                    self.__init__(self.controller)
                    play_music()
                return

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
                if self.move_down():
                     self.score +=1
                self.move_time = pygame.time.get_ticks()
            elif event.key == pygame.K_UP:
                self.rotate_piece()
            elif event.key == pygame.K_SPACE:
                self.drop_piece()
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                current_volume = pygame.mixer.music.get_volume()
                new_volume = min(1.0, current_volume + 0.1)
                pygame.mixer.music.set_volume(new_volume)
                # Also set sound effects volume if desired
                # for sound in self.sounds.values(): sound.set_volume(new_volume)
            elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                current_volume = pygame.mixer.music.get_volume()
                new_volume = max(0.0, current_volume - 0.1)
                pygame.mixer.music.set_volume(new_volume)
                # for sound in self.sounds.values(): sound.set_volume(new_volume)
            elif event.key == pygame.K_m:
                if pygame.mixer.music.get_volume() > 0:
                    pygame.mixer.music.set_volume(0.0)
                    # for sound in self.sounds.values(): sound.set_volume(0.0)
                else:
                    pygame.mixer.music.set_volume(0.7) # Default volume
                    # for sound in self.sounds.values(): sound.set_volume(0.5) # Default volume

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.left_pressed = False
            elif event.key == pygame.K_RIGHT:
                self.right_pressed = False
            elif event.key == pygame.K_DOWN:
                self.down_pressed = False

        if self.controller:
            if event.type == pygame.JOYBUTTONDOWN:
                if self.controller.get_button(9): # Start button
                    if not self.game_over:
                        if not self.paused:
                            self.paused = True
                            self.paused_start_time = pygame.time.get_ticks()
                            stop_music()
                        else:
                            self.paused = False
                            self.time_spent_paused += pygame.time.get_ticks() - self.paused_start_time
                            play_music()
                    return
                
                if self.paused and not (self.controller.get_button(9)): return

                if self.game_over:
                    if self.controller.get_button(8): # Share button for restart
                        self.__init__(self.controller)
                        play_music()
                    return

                if self.controller.get_button(3): # Triangle for rotate
                    self.rotate_piece()
                elif self.controller.get_button(0): # X button for hard drop
                    self.drop_piece()

            if self.paused : return # Ignore axis/hat if paused
            
            if event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = self.controller.get_hat(0)
                self.left_pressed = (hat_x == -1)
                self.right_pressed = (hat_x == 1)
                self.down_pressed = (hat_y == -1) # D-pad down for soft drop

                if hat_x == -1:
                    self.move_left()
                    self.move_time = pygame.time.get_ticks()
                elif hat_x == 1:
                    self.move_right()
                    self.move_time = pygame.time.get_ticks()
                if hat_y == -1: # Soft drop with D-pad
                    if self.move_down():
                        self.score +=1
                    self.move_time = pygame.time.get_ticks()
            
            if event.type == pygame.JOYAXISMOTION:
                if self.paused: return # Ignore axis motion if paused
                
                # Left analog stick
                left_stick_x = self.controller.get_axis(0)
                left_stick_y = self.controller.get_axis(1) # Y-axis for soft drop
                deadzone = 0.5

                if left_stick_x < -deadzone:
                    if not self.left_pressed: # Prevent rapid re-triggering if already moving
                        self.left_pressed = True; self.right_pressed = False
                        self.move_left(); self.move_time = pygame.time.get_ticks()
                elif left_stick_x > deadzone:
                    if not self.right_pressed:
                        self.right_pressed = True; self.left_pressed = False
                        self.move_right(); self.move_time = pygame.time.get_ticks()
                else:
                    self.left_pressed = False; self.right_pressed = False
                
                if left_stick_y > deadzone: # Analog stick down for soft drop
                    if not self.down_pressed:
                        self.down_pressed = True
                        if self.move_down():
                            self.score +=1
                        self.move_time = pygame.time.get_ticks()
                else:
                    self.down_pressed = False


    def draw_grid(self, screen, offset_x, offset_y):
        pygame.draw.rect(screen, BLACK, (offset_x, offset_y, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))
        for y_idx in range(GRID_HEIGHT):
            for x_idx in range(GRID_WIDTH):
                if self.grid[y_idx][x_idx]:
                    color_idx = self.grid[y_idx][x_idx] - 1
                    pygame.draw.rect(screen, COLORS[color_idx % len(COLORS)],
                                     (offset_x + x_idx * CELL_SIZE, offset_y + y_idx * CELL_SIZE,
                                      CELL_SIZE - 1, CELL_SIZE - 1))
        if not self.game_over and self.current_piece: # Check if current_piece is not None
            for y_offset, row in enumerate(self.current_piece):
                for x_offset, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(screen, COLORS[self.color_index % len(COLORS)],
                                         (offset_x + (self.piece_x + x_offset) * CELL_SIZE,
                                          offset_y + (self.piece_y + y_offset) * CELL_SIZE,
                                          CELL_SIZE - 1, CELL_SIZE - 1))
        pygame.draw.rect(screen, WHITE, (offset_x, offset_y, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE), 2)

    def draw_next_piece(self, screen, offset_x, offset_y):
        # Ensure next_piece and its color_index exist
        if not self.next_piece or self.next_color_index is None:
            return

        preview_box_total_width = PREVIEW_SIZE * CELL_SIZE
        preview_box_total_height = PREVIEW_SIZE * CELL_SIZE # Make it square for consistency
        
        # Background for the preview box
        pygame.draw.rect(screen, BLACK, (offset_x, offset_y, preview_box_total_width, preview_box_total_height))
        pygame.draw.rect(screen, WHITE, (offset_x, offset_y, preview_box_total_width, preview_box_total_height), 2)

        piece_width_cells = len(self.next_piece[0])
        piece_height_cells = len(self.next_piece)
        
        # Calculate offsets to center the piece within the preview box
        start_x_offset_in_box = (preview_box_total_width - (piece_width_cells * CELL_SIZE)) // 2
        start_y_offset_in_box = (preview_box_total_height - (piece_height_cells * CELL_SIZE)) // 2
        
        draw_start_x = offset_x + start_x_offset_in_box
        draw_start_y = offset_y + start_y_offset_in_box

        for y, row in enumerate(self.next_piece):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, COLORS[self.next_color_index % len(COLORS)],
                                     (draw_start_x + x * CELL_SIZE, 
                                      draw_start_y + y * CELL_SIZE,
                                      CELL_SIZE - 1, CELL_SIZE - 1))

    def draw_info(self, screen, panel_base_x, panel_base_y):
        """Draw game information: score, level, time, and next piece preview."""
        info_panel_width = PANEL_WIDTH - INFO_PADDING * 2 # Actual drawable width inside panel
        
        # Score Panel Background (adjust height as needed)
        score_panel_height = 180 # Increased height for timer
        score_bg_rect_x = panel_base_x + INFO_PADDING
        score_bg_rect_y = panel_base_y + INFO_PADDING
        
        score_bg = pygame.Surface((info_panel_width, score_panel_height))
        score_bg.fill(GRAY)
        pygame.draw.rect(score_bg, WHITE, score_bg.get_rect(), 2)
        
        # Score Text
        score_text_render = self.font_big.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text_render.get_rect(midtop=(info_panel_width // 2, INFO_PADDING))
        score_bg.blit(score_text_render, score_rect)
        
        # Level Text
        level_text_render = self.font_medium.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text_render.get_rect(midtop=(info_panel_width // 2, score_rect.bottom + 5))
        score_bg.blit(level_text_render, level_rect)
        
        # Timer Text
        minutes = self.total_time // 60000
        seconds = (self.total_time % 60000) // 1000
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        time_text_render = self.font_medium.render(time_str, True, WHITE)
        time_rect = time_text_render.get_rect(midtop=(info_panel_width // 2, level_rect.bottom + 5))
        score_bg.blit(time_text_render, time_rect)
        
        screen.blit(score_bg, (score_bg_rect_x, score_bg_rect_y))
        
        # Next Piece Preview
        next_piece_label_text = self.font_medium.render("Next:", True, WHITE)
        next_piece_label_rect = next_piece_label_text.get_rect(left=score_bg_rect_x, top=score_bg_rect_y + score_panel_height + INFO_PADDING)
        screen.blit(next_piece_label_text, next_piece_label_rect)
        
        # Position next piece preview box below the label
        next_piece_box_x = score_bg_rect_x
        next_piece_box_y = next_piece_label_rect.bottom + 5 # Small padding
        self.draw_next_piece(screen, next_piece_box_x, next_piece_box_y)

        # Note: draw_controls is now called directly in the run loop to avoid duplication
        # self.draw_controls(screen, panel_base_x + INFO_PADDING, next_piece_box_y + PREVIEW_SIZE * CELL_SIZE + INFO_PADDING * 2)


    def draw_controls(self, screen, offset_x, offset_y):
        title_text = self.font_medium.render("Controls:", True, WHITE)
        screen.blit(title_text, (offset_x, offset_y))
        y_spacing = 20
        current_y = offset_y + title_text.get_height() + 5

        controls = []
        if self.controller:
            controls = [
                "D-Pad/Stick: Move",
                "Triangle (Btn 3): Rotate",
                "X (Btn 0): Hard Drop",
                "Start (Btn 9): Pause",
                "Share (Btn 8): Restart (Game Over)"
            ]
        else:
            controls = [
                "Arrow Keys: Move",
                "Up Arrow: Rotate",
                "Space: Hard Drop",
                "P: Pause",
                "R: Restart (Game Over)"
            ]

        for control in controls:
            control_text = self.font_small.render(control, True, WHITE)
            screen.blit(control_text, (offset_x, current_y))
            current_y += y_spacing

    def draw_game_over(self, screen, width, height):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        game_over_text = self.font_big.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(width // 2, height // 2 - 60))
        screen.blit(game_over_text, text_rect)

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(width // 2, height // 2 - 20))
        screen.blit(score_text, score_rect)
        
        minutes = self.total_time // 60000
        seconds = (self.total_time % 60000) // 1000
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        time_text_render = self.font_medium.render(time_str, True, WHITE)
        time_rect = time_text_render.get_rect(center=(width // 2, score_rect.bottom + 20))
        screen.blit(time_text_render, time_rect)


        restart_instruction = "Press Share (Controller) or R (Keyboard) to Restart"
        if self.controller:
             restart_text_render = self.font_medium.render("Press Share Button to Restart", True, WHITE)
        else:
             restart_text_render = self.font_medium.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text_render.get_rect(center=(width // 2, time_rect.bottom + 30))
        screen.blit(restart_text_render, restart_rect)

    def draw_pause(self, screen, width, height):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pause_text_render = self.font_big.render("PAUSED", True, WHITE)
        text_rect = pause_text_render.get_rect(center=(width // 2, height // 2 - 30))
        screen.blit(pause_text_render, text_rect)

        if self.controller:
            continue_text = self.font_medium.render("Press Start Button to Continue", True, WHITE)
        else:
            continue_text = self.font_medium.render("Press P to Continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(width // 2, height // 2 + 20))
        screen.blit(continue_text, continue_rect)

    def check_controller(self):
        if not self.controller or not self.controller.get_init():
            pygame.joystick.quit()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                try:
                    self.controller = pygame.joystick.Joystick(0)
                    self.controller.init()
                except pygame.error:
                    self.controller = None # Handle case where joystick init fails
            else:
                self.controller = None

    def run(self, screen_surface): # Renamed screen to screen_surface to avoid conflict
        # Calculate window size and positions
        # Use PANEL_HEIGHT which is max(GRID_HEIGHT * CELL_SIZE, 350)
        # Ensure PANEL_HEIGHT is enough for score_panel + next_piece_preview + controls_text + margins
        required_panel_content_height = (180 + # score panel
                                        INFO_PADDING + # space
                                        self.font_medium.get_height() + 5 + # "Next:" label
                                        PREVIEW_SIZE * CELL_SIZE + # Next piece box
                                        INFO_PADDING + # space
                                        self.font_medium.get_height() + 5 + (5 * 20) + # Controls title and 5 lines
                                        INFO_PADDING) # bottom padding
                                        
        actual_panel_height = max(GRID_HEIGHT * CELL_SIZE, required_panel_content_height)


        window_width = OUTER_MARGIN * 2 + GRID_WIDTH * CELL_SIZE + PANEL_MARGIN + PANEL_WIDTH
        # window_height = OUTER_MARGIN * 2 + GRID_HEIGHT * CELL_SIZE # Original
        window_height = OUTER_MARGIN * 2 + actual_panel_height # Use calculated panel height


        # Re-set mode with potentially new height
        current_screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Tetris - Single Player")


        grid_x = OUTER_MARGIN
        grid_y = OUTER_MARGIN
        
        panel_base_x = grid_x + GRID_WIDTH * CELL_SIZE + PANEL_MARGIN
        panel_base_y = grid_y # Align panel top with grid top

        # Calculate Y position for controls, ensuring it's at the bottom of the panel area
        # controls_y_offset = panel_base_y + INFO_PADDING + 180 + INFO_PADDING + self.font_medium.get_height() + 5 + PREVIEW_SIZE * CELL_SIZE + INFO_PADDING
        # Fixed controls_y positioning:
        next_piece_box_height_with_label = self.font_medium.get_height() + 5 + PREVIEW_SIZE * CELL_SIZE
        controls_y_offset = panel_base_y + INFO_PADDING + 180 + INFO_PADDING + next_piece_box_height_with_label + INFO_PADDING * 2


        play_music()
        running = True
        while running:
            self.check_controller()
            ensure_music_playing()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False; stop_music(); return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False; stop_music(); return
                if self.controller and event.type == pygame.JOYBUTTONDOWN:
                    if self.controller.get_button(1): # Circle for back/escape
                        running = False; stop_music(); return
                self.handle_input(event)

            self.update()
            current_screen.fill(GRAY)

            # Volume info text
            volume_info_text = self.font_small.render("Volume: +/- (M to mute)", True, WHITE)
            volume_rect = volume_info_text.get_rect(center=(window_width // 2, window_height - 20))
            current_screen.blit(volume_info_text, volume_rect)

            self.draw_grid(current_screen, grid_x, grid_y)
            self.draw_info(current_screen, panel_base_x, panel_base_y) 
            self.draw_controls(current_screen, panel_base_x + INFO_PADDING, controls_y_offset)


            if self.paused:
                self.draw_pause(current_screen, window_width, window_height)
            elif self.game_over:
                self.draw_game_over(current_screen, window_width, window_height)

            pygame.display.flip()
            self.clock.tick(60)

def single_player_mode():
    pygame.init()
    if not pygame.mixer.get_init(): # Initialize mixer only if not already initialized
        pygame.mixer.init()

    controller = None
    pygame.joystick.init()
    if pygame.joystick.get_count() > 0:
        try:
            controller = pygame.joystick.Joystick(0)
            controller.init()
        except pygame.error:
            print("Could not initialize controller.")
            controller = None
            
    # Create a dummy screen initially, SinglePlayerGame.run will set the correct one
    screen = pygame.display.set_mode((800, 650)) # Adjusted initial height slightly
    
    game = SinglePlayerGame(controller)
    game.run(screen)