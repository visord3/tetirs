# multiplayer.py
import sys
import pygame
import random

# Import from the updated single_player module
from single_player import COLORS, SHAPES, CELL_SIZE, LEVEL_SPEED


#########################
# Helper functions to replace the imported ones from the old single_player
#########################
def spawn_block(grid):
    """Generate a new Tetris piece for multiplayer"""
    shape_idx = random.randint(0, len(SHAPES) - 1)
    shape = [row[:] for row in SHAPES[shape_idx]]
    color = COLORS[shape_idx]
    x = len(grid[0]) // 2 - len(shape[0]) // 2
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
        original_shape = [row[:] for row in self.shape]

        # Transpose and reverse rows for clockwise rotation
        rotated = list(zip(*self.shape[::-1]))
        self.shape = [list(row) for row in rotated]

        # Check if rotation is valid
        if not self.is_valid_position(grid):
            # Restore original shape if rotation causes collision
            self.shape = original_shape

    def is_valid_position(self, grid):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = self.col_offset + x
                    grid_y = self.row_offset + y

                    # Check if out of bounds
                    if (grid_x < 0 or grid_x >= len(grid[0]) or
                            grid_y >= len(grid) or
                            (grid_y >= 0 and grid[grid_y][grid_x])):
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
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x]:
                    pygame.draw.rect(
                        screen,
                        self.grid[y][x],  # Color stored in grid
                        (
                            offset_x + x * self.cell_size,
                            offset_y + y * self.cell_size,
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
        for y, row in enumerate(block.shape):
            for x, cell in enumerate(row):
                if cell and 0 <= block.row_offset + y < self.height:
                    self.grid[block.row_offset + y][block.col_offset + x] = block.color

    def clear_rows(self):
        lines_cleared = 0
        y = self.height - 1
        while y >= 0:
            if all(cell != 0 for cell in self.grid[y]):
                # Move all lines above down
                for move_y in range(y, 0, -1):
                    self.grid[move_y] = self.grid[move_y - 1][:]
                # Clear the top line
                self.grid[0] = [0] * self.width
                lines_cleared += 1
            else:
                y -= 1

        return lines_cleared


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

    while running:
        dt = clock.tick(60)
        if button_cooldown > 0:
            button_cooldown -= dt

        screen.fill((0, 0, 0))

        # Display winner text
        if winner == "tie":
            end_text = font.render("It's a tie!", True, (255, 255, 255))
        else:
            end_text = font.render(f"{winner} Wins!", True, (255, 255, 255))
        end_rect = end_text.get_rect(center=(width // 2, height // 2 - 50))
        screen.blit(end_text, end_rect)

        # Play Again button
        play_again_button = pygame.Rect(150, 300, 300, 50)
        play_again_color = (100, 100, 255) if selected_option == 0 else (255, 255, 255)
        pygame.draw.rect(screen, play_again_color, play_again_button)
        play_again_text = font.render("Play Again", True, (0, 0, 0))
        play_again_rect = play_again_text.get_rect(center=play_again_button.center)
        screen.blit(play_again_text, play_again_rect)

        # Quit button
        quit_button = pygame.Rect(150, 400, 300, 50)
        quit_color = (100, 100, 255) if selected_option == 1 else (255, 255, 255)
        pygame.draw.rect(screen, quit_color, quit_button)
        quit_text = font.render("Quit", True, (0, 0, 0))
        quit_rect = quit_text.get_rect(center=quit_button.center)
        screen.blit(quit_text, quit_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Keyboard controls
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                    selected_option = 1 - selected_option  # Toggle between 0 and 1
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
                        button_cooldown = cooldown_time

                # Analog stick navigation
                if event.type == pygame.JOYAXISMOTION:
                    left_stick_y = controller.get_axis(1)
                    deadzone = 0.5

                    if abs(left_stick_y) > deadzone and button_cooldown <= 0:
                        selected_option = 1 if left_stick_y > 0 else 0
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
# MULTIPLAYER MODE
#########################
def multiplayer_mode():
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600

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

    clock = pygame.time.Clock()
    running = True

    # Create the two 10x20 grids
    player1_grid = Grid(10, 20, CELL_SIZE)
    player2_grid = Grid(10, 20, CELL_SIZE)

    score_p1 = 0
    score_p2 = 0
    total_lines_p1 = 0
    total_lines_p2 = 0
    level_p1 = 1
    level_p2 = 1

    # Game duration in seconds
    timer = 120  # 2 minutes
    start_ticks = pygame.time.get_ticks()

    # Spawn initial blocks for both players
    block_p1 = spawn_block(player1_grid.grid)
    block_p2 = spawn_block(player2_grid.grid)

    # Fall speeds and last drop times for each player
    fall_speed_p1 = adjust_fall_speed(total_lines_p1)  # ms
    fall_speed_p2 = adjust_fall_speed(total_lines_p2)  # ms
    last_drop_time_p1 = pygame.time.get_ticks()
    last_drop_time_p2 = pygame.time.get_ticks()

    # Input state tracking
    p1_left_pressed = False
    p1_right_pressed = False
    p1_down_pressed = False
    p2_left_pressed = False
    p2_right_pressed = False
    p2_down_pressed = False
    move_delay = 100  # ms
    p1_move_time = pygame.time.get_ticks()
    p2_move_time = pygame.time.get_ticks()

    # Font for game info
    font = pygame.font.SysFont("Arial", 24)
    title_font = pygame.font.SysFont("Arial", 36)

    while running:
        now = pygame.time.get_ticks()
        elapsed_time = (now - start_ticks) // 1000
        remaining_time = max(0, timer - elapsed_time)

        if remaining_time <= 0 and running:
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            # ESC to return to main menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            ###############
            # Keyboard Controls
            ###############
            if event.type == pygame.KEYDOWN:
                # Player 1 Controls
                if block_p1:
                    if event.key == pygame.K_LEFT:
                        p1_left_pressed = True
                        p1_right_pressed = False
                        block_p1.col_offset -= 1
                        if not block_p1.is_valid_position(player1_grid.grid):
                            block_p1.col_offset += 1
                        p1_move_time = now
                    elif event.key == pygame.K_RIGHT:
                        p1_left_pressed = False
                        p1_right_pressed = True
                        block_p1.col_offset += 1
                        if not block_p1.is_valid_position(player1_grid.grid):
                            block_p1.col_offset -= 1
                        p1_move_time = now
                    elif event.key == pygame.K_DOWN:
                        p1_down_pressed = True
                        block_p1.row_offset += 1
                        if not block_p1.is_valid_position(player1_grid.grid):
                            block_p1.row_offset -= 1
                            player1_grid.place_block(block_p1)
                            lines_cleared = player1_grid.clear_rows()
                            if lines_cleared:
                                total_lines_p1 += lines_cleared
                                level_p1 = min(10, total_lines_p1 // 10 + 1)
                                score_p1 += get_line_clear_score(lines_cleared, level_p1)
                                fall_speed_p1 = adjust_fall_speed(total_lines_p1)

                            block_p1 = spawn_block(player1_grid.grid)
                        p1_move_time = now
                    elif event.key == pygame.K_UP:
                        block_p1.rotate(player1_grid.grid)
                    elif event.key == pygame.K_SPACE:  # Hard drop
                        while block_p1.is_valid_position(player1_grid.grid):
                            block_p1.row_offset += 1
                        block_p1.row_offset -= 1
                        player1_grid.place_block(block_p1)
                        lines_cleared = player1_grid.clear_rows()
                        if lines_cleared:
                            total_lines_p1 += lines_cleared
                            level_p1 = min(10, total_lines_p1 // 10 + 1)
                            score_p1 += get_line_clear_score(lines_cleared, level_p1)
                            fall_speed_p1 = adjust_fall_speed(total_lines_p1)
                        block_p1 = spawn_block(player1_grid.grid)

                # Player 2 Controls
                if block_p2:
                    if event.key == pygame.K_a:
                        p2_left_pressed = True
                        p2_right_pressed = False
                        block_p2.col_offset -= 1
                        if not block_p2.is_valid_position(player2_grid.grid):
                            block_p2.col_offset += 1
                        p2_move_time = now
                    elif event.key == pygame.K_d:
                        p2_left_pressed = False
                        p2_right_pressed = True
                        block_p2.col_offset += 1
                        if not block_p2.is_valid_position(player2_grid.grid):
                            block_p2.col_offset -= 1
                        p2_move_time = now
                    elif event.key == pygame.K_s:
                        p2_down_pressed = True
                        block_p2.row_offset += 1
                        if not block_p2.is_valid_position(player2_grid.grid):
                            block_p2.row_offset -= 1
                            player2_grid.place_block(block_p2)
                            lines_cleared = player2_grid.clear_rows()
                            if lines_cleared:
                                total_lines_p2 += lines_cleared
                                level_p2 = min(10, total_lines_p2 // 10 + 1)
                                score_p2 += get_line_clear_score(lines_cleared, level_p2)
                                fall_speed_p2 = adjust_fall_speed(total_lines_p2)
                            block_p2 = spawn_block(player2_grid.grid)
                        p2_move_time = now
                    elif event.key == pygame.K_w:
                        block_p2.rotate(player2_grid.grid)
                    elif event.key == pygame.K_f:  # Hard drop for P2
                        while block_p2.is_valid_position(player2_grid.grid):
                            block_p2.row_offset += 1
                        block_p2.row_offset -= 1
                        player2_grid.place_block(block_p2)
                        lines_cleared = player2_grid.clear_rows()
                        if lines_cleared:
                            total_lines_p2 += lines_cleared
                            level_p2 = min(10, total_lines_p2 // 10 + 1)
                            score_p2 += get_line_clear_score(lines_cleared, level_p2)
                            fall_speed_p2 = adjust_fall_speed(total_lines_p2)
                        block_p2 = spawn_block(player2_grid.grid)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    p1_left_pressed = False
                elif event.key == pygame.K_RIGHT:
                    p1_right_pressed = False
                elif event.key == pygame.K_DOWN:
                    p1_down_pressed = False
                elif event.key == pygame.K_a:
                    p2_left_pressed = False
                elif event.key == pygame.K_d:
                    p2_right_pressed = False
                elif event.key == pygame.K_s:
                    p2_down_pressed = False

            ###############
            # Controller Controls (only for Player 1 if using split screen)
            ###############
            if controller:
                # D-pad for Player 1
                if event.type == pygame.JOYHATMOTION and block_p1:
                    hat_x, hat_y = controller.get_hat(0)

                    p1_left_pressed = (hat_x == -1)
                    p1_right_pressed = (hat_x == 1)
                    p1_down_pressed = (hat_y == -1)

                    if hat_x == -1:
                        block_p1.col_offset -= 1
                        if not block_p1.is_valid_position(player1_grid.grid):
                            block_p1.col_offset += 1
                        else:
                            p1_move_time = now
                    elif hat_x == 1:
                        block_p1.col_offset += 1
                        if not block_p1.is_valid_position(player1_grid.grid):
                            block_p1.col_offset -= 1
                        else:
                            p1_move_time = now

                    if hat_y == -1:
                        block_p1.row_offset += 1
                        if not block_p1.is_valid_position(player1_grid.grid):
                            block_p1.row_offset -= 1
                            player1_grid.place_block(block_p1)
                            lines_cleared = player1_grid.clear_rows()
                            if lines_cleared:
                                total_lines_p1 += lines_cleared
                                level_p1 = min(10, total_lines_p1 // 10 + 1)
                                score_p1 += get_line_clear_score(lines_cleared, level_p1)
                                fall_speed_p1 = adjust_fall_speed(total_lines_p1)
                            block_p1 = spawn_block(player1_grid.grid)
                        p1_move_time = now

                # Analog stick for Player 1
                if event.type == pygame.JOYAXISMOTION and block_p1:
                    left_stick_x = controller.get_axis(0)
                    left_stick_y = controller.get_axis(1)
                    deadzone = 0.5

                    # X-axis (left/right)
                    if left_stick_x < -deadzone:
                        if not p1_left_pressed:
                            p1_left_pressed = True
                            p1_right_pressed = False
                            block_p1.col_offset -= 1
                            if not block_p1.is_valid_position(player1_grid.grid):
                                block_p1.col_offset += 1
                            else:
                                p1_move_time = now
                    elif left_stick_x > deadzone:
                        if not p1_right_pressed:
                            p1_left_pressed = False
                            p1_right_pressed = True
                            block_p1.col_offset += 1
                            if not block_p1.is_valid_position(player1_grid.grid):
                                block_p1.col_offset -= 1
                            else:
                                p1_move_time = now
                    else:
                        p1_left_pressed = False
                        p1_right_pressed = False

                    # Y-axis (down)
                    if left_stick_y > deadzone:
                        if not p1_down_pressed:
                            p1_down_pressed = True
                            block_p1.row_offset += 1
                            if not block_p1.is_valid_position(player1_grid.grid):
                                block_p1.row_offset -= 1
                                player1_grid.place_block(block_p1)
                                lines_cleared = player1_grid.clear_rows()
                                if lines_cleared:
                                    total_lines_p1 += lines_cleared
                                    level_p1 = min(10, total_lines_p1 // 10 + 1)
                                    score_p1 += get_line_clear_score(lines_cleared, level_p1)
                                    fall_speed_p1 = adjust_fall_speed(total_lines_p1)
                                block_p1 = spawn_block(player1_grid.grid)
                            p1_move_time = now
                    else:
                        p1_down_pressed = False

                # Button presses for Player 1
                if event.type == pygame.JOYBUTTONDOWN and block_p1:
                    # Triangle (3) to rotate
                    if controller.get_button(3):
                        block_p1.rotate(player1_grid.grid)

                    # X button (0) for hard drop
                    elif controller.get_button(0):
                        while block_p1.is_valid_position(player1_grid.grid):
                            block_p1.row_offset += 1
                        block_p1.row_offset -= 1
                        player1_grid.place_block(block_p1)
                        lines_cleared = player1_grid.clear_rows()
                        if lines_cleared:
                            total_lines_p1 += lines_cleared
                            level_p1 = min(10, total_lines_p1 // 10 + 1)
                            score_p1 += get_line_clear_score(lines_cleared, level_p1)
                            fall_speed_p1 = adjust_fall_speed(total_lines_p1)
                        block_p1 = spawn_block(player1_grid.grid)

        ######################
        # Handle continuous movement when directions are held
        ######################
        # Player 1
        if block_p1 and now - p1_move_time > move_delay:
            if p1_left_pressed:
                block_p1.col_offset -= 1
                if not block_p1.is_valid_position(player1_grid.grid):
                    block_p1.col_offset += 1
                else:
                    p1_move_time = now
            elif p1_right_pressed:
                block_p1.col_offset += 1
                if not block_p1.is_valid_position(player1_grid.grid):
                    block_p1.col_offset -= 1
                else:
                    p1_move_time = now
            elif p1_down_pressed:
                block_p1.row_offset += 1
                if not block_p1.is_valid_position(player1_grid.grid):
                    block_p1.row_offset -= 1
                    player1_grid.place_block(block_p1)
                    lines_cleared = player1_grid.clear_rows()
                    if lines_cleared:
                        total_lines_p1 += lines_cleared
                        level_p1 = min(10, total_lines_p1 // 10 + 1)
                        score_p1 += get_line_clear_score(lines_cleared, level_p1)
                        fall_speed_p1 = adjust_fall_speed(total_lines_p1)
                    block_p1 = spawn_block(player1_grid.grid)
                else:
                    p1_move_time = now

        # Player 2
        if block_p2 and now - p2_move_time > move_delay:
            if p2_left_pressed:
                block_p2.col_offset -= 1
                if not block_p2.is_valid_position(player2_grid.grid):
                    block_p2.col_offset += 1
                else:
                    p2_move_time = now
            elif p2_right_pressed:
                block_p2.col_offset += 1
                if not block_p2.is_valid_position(player2_grid.grid):
                    block_p2.col_offset -= 1
                else:
                    p2_move_time = now
            elif p2_down_pressed:
                block_p2.row_offset += 1
                if not block_p2.is_valid_position(player2_grid.grid):
                    block_p2.row_offset -= 1
                    player2_grid.place_block(block_p2)
                    lines_cleared = player2_grid.clear_rows()
                    if lines_cleared:
                        total_lines_p2 += lines_cleared
                        level_p2 = min(10, total_lines_p2 // 10 + 1)
                        score_p2 += get_line_clear_score(lines_cleared, level_p2)
                        fall_speed_p2 = adjust_fall_speed(total_lines_p2)
                    block_p2 = spawn_block(player2_grid.grid)
                else:
                    p2_move_time = now

        ######################
        # Timed auto-drop for P1
        ######################
        if block_p1 and (now - last_drop_time_p1 >= fall_speed_p1):
            block_p1.row_offset += 1
            if not block_p1.is_valid_position(player1_grid.grid):
                block_p1.row_offset -= 1
                player1_grid.place_block(block_p1)
                lines_cleared = player1_grid.clear_rows()
                if lines_cleared:
                    total_lines_p1 += lines_cleared
                    level_p1 = min(10, total_lines_p1 // 10 + 1)
                    score_p1 += get_line_clear_score(lines_cleared, level_p1)
                    fall_speed_p1 = adjust_fall_speed(total_lines_p1)
                block_p1 = spawn_block(player1_grid.grid)
            last_drop_time_p1 = now

        ######################
        # Timed auto-drop for P2
        ######################
        if block_p2 and (now - last_drop_time_p2 >= fall_speed_p2):
            block_p2.row_offset += 1
            if not block_p2.is_valid_position(player2_grid.grid):
                block_p2.row_offset -= 1
                player2_grid.place_block(block_p2)
                lines_cleared = player2_grid.clear_rows()
                if lines_cleared:
                    total_lines_p2 += lines_cleared
                    level_p2 = min(10, total_lines_p2 // 10 + 1)
                    score_p2 += get_line_clear_score(lines_cleared, level_p2)
                    fall_speed_p2 = adjust_fall_speed(total_lines_p2)
                block_p2 = spawn_block(player2_grid.grid)
            last_drop_time_p2 = now

        #########################
        # DRAWING
        #########################
        screen.fill((50, 50, 50))  # Dark gray background

        # Draw title
        title_text = title_font.render("MULTIPLAYER TETRIS", True, (255, 255, 100))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
        screen.blit(title_text, title_rect)

        # Calculate grid offsets
        grid_width = player1_grid.width * CELL_SIZE
        grid_height = player1_grid.height * CELL_SIZE
        p1_offset_x = (SCREEN_WIDTH // 2 - grid_width) // 2
        p2_offset_x = SCREEN_WIDTH // 2 + (SCREEN_WIDTH // 2 - grid_width) // 2
        grid_offset_y = 70  # Leave space for title and scores

        # Draw each grid
        player1_grid.draw(screen, offset_x=p1_offset_x, offset_y=grid_offset_y)
        player2_grid.draw(screen, offset_x=p2_offset_x, offset_y=grid_offset_y)

        # Draw the vertical dividing line in the middle
        pygame.draw.line(
            screen,
            (255, 255, 255),  # white
            (SCREEN_WIDTH // 2, 0),  # start at top center
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT),  # down to bottom center
            2  # line thickness
        )

        # Draw blocks
        if block_p1:
            block_p1.draw(screen, offset_x=p1_offset_x, offset_y=grid_offset_y)
        if block_p2:
            block_p2.draw(screen, offset_x=p2_offset_x, offset_y=grid_offset_y)

        # Draw player labels and scores
        p1_label = font.render("PLAYER 1", True, (255, 255, 255))
        p2_label = font.render("PLAYER 2", True, (255, 255, 255))
        screen.blit(p1_label, (p1_offset_x, grid_offset_y - 30))
        screen.blit(p2_label, (p2_offset_x, grid_offset_y - 30))

        # Scores
        score_text_p1 = font.render(f"Score: {score_p1}", True, (255, 255, 255))
        score_text_p2 = font.render(f"Score: {score_p2}", True, (255, 255, 255))
        level_text_p1 = font.render(f"Level: {level_p1}", True, (255, 255, 255))
        level_text_p2 = font.render(f"Level: {level_p2}", True, (255, 255, 255))
        lines_text_p1 = font.render(f"Lines: {total_lines_p1}", True, (255, 255, 255))
        lines_text_p2 = font.render(f"Lines: {total_lines_p2}", True, (255, 255, 255))

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

        pygame.display.flip()
        clock.tick(60)

    # Determine winner after time runs out or block spawn fails
    if score_p1 > score_p2:
        winner = "Player 1"
    elif score_p2 > score_p1:
        winner = "Player 2"
    else:
        winner = "tie"

    # Show end screen and handle replay
    if show_end_screen(screen, winner, SCREEN_WIDTH, SCREEN_HEIGHT):
        multiplayer_mode()  # Restart the mode if "Play Again" clicked