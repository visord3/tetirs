# multiplayer.py - Improved multiplayer mode with proper game loop
import sys
import pygame
import random
import os

# Import game components
from grid import Grid
from colors import Colors # Assuming this defines color tuples like WHITE, GRAY etc.
# from constants import * # Be specific about what you import or define them here
# from player import Player # This is the simple player.py, not the one within multiplayer.py

# Define constants if not imported fully from constants.py
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PREVIEW_SIZE = 4 # For next piece preview
LEVEL_SPEED = [1000, 800, 600, 500, 400, 300, 250, 200, 150, 100] # ms per drop

# Layout constants for multiplayer
PANEL_INFO_WIDTH = 200 # Width for each player's info panel (score, level, next)
PANEL_CONTROLS_HEIGHT = 150 # Approximate height for controls display area
FIELD_MARGIN_HORIZONTAL = 50 # Margin between the two game fields
OUTER_MARGIN_HORIZONTAL = 40
OUTER_MARGIN_VERTICAL = 40
INFO_PADDING = 10 # Padding inside info panels

# Derived layout values
GAME_FIELD_WIDTH_PX = GRID_WIDTH * CELL_SIZE
GAME_FIELD_HEIGHT_PX = GRID_HEIGHT * CELL_SIZE

# Total window dimensions will be calculated in multiplayer_mode

# Color definitions (ensure these are available)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50) # Darker gray for background
LIGHT_GRAY = (100, 100, 100) # For panel backgrounds
RED = (255, 0, 0)
# Add other colors if needed from your Colors class or define here

# Import sound manager
from sound_manager import load_game_sounds, play_sound, play_music, stop_music, ensure_music_playing


# get_random_block function (ensure it's compatible with your Block class structure)
def get_random_block_multiplayer(cell_size_param): # Renamed to avoid conflict if block.py also has one
    from blocks import IBlock, OBlock, TBlock, SBlock, ZBlock, JBlock, LBlock # Assuming blocks.py exists
    block_classes = [IBlock, OBlock, TBlock, SBlock, ZBlock, JBlock, LBlock]
    chosen_block_class = random.choice(block_classes)
    return chosen_block_class(cell_size_param) # Pass cell_size to block constructor


class MultiplayerPlayer: # Renamed to avoid clash with player.py's Player
    def __init__(self, player_id, grid_width_cells=GRID_WIDTH, grid_height_cells=GRID_HEIGHT, cell_pixel_size=CELL_SIZE):
        self.player_id = player_id
        self.grid = Grid(grid_width_cells, grid_height_cells, cell_pixel_size) # from grid.py
        self.current_block = None
        self.next_block = None
        
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.active = True # Is player still in the game?
        
        self.fall_speed_ms = LEVEL_SPEED[0]
        self.last_drop_event_time = pygame.time.get_ticks()
        self.last_move_event_time = pygame.time.get_ticks() # For continuous horizontal/down movement
        
        self.input_left_pressed = False
        self.input_right_pressed = False
        self.input_down_pressed = False
        
        # Fonts (can be passed in or initialized here)
        self.font_panel_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_panel_info = pygame.font.SysFont("Arial", 22)
        self.font_controls = pygame.font.SysFont("Arial", 16)

        self.cell_size = cell_pixel_size # Store cell_size for drawing next block
        
        self.spawn_new_block() # Initial current block
        self.spawn_new_block() # Initial next block (current becomes next, new next is generated)
    
    def spawn_new_block(self):
        if self.next_block:
            self.current_block = self.next_block
        else:
            # This case should ideally only happen on first spawn if next_block wasn't pre-generated
            self.current_block = get_random_block_multiplayer(self.cell_size) 
        
        self.next_block = get_random_block_multiplayer(self.cell_size) # from blocks.py
        
        # Position new block at top-center of grid
        # Assuming block.py's Block class has col_offset, row_offset, and is_valid_position
        self.current_block.col_offset = self.grid.num_cols // 2 # Needs adjustment based on block width
        # Adjust for block width:
        if self.current_block.cells and 0 in self.current_block.cells: # Check if rotation 0 exists
            current_shape_cells = self.current_block.cells[0]
            if current_shape_cells: # Check if the shape has cells
                 min_col = min(p.col for p in current_shape_cells)
                 max_col = max(p.col for p in current_shape_cells)
                 block_width_in_cells = max_col - min_col + 1
                 self.current_block.col_offset = (self.grid.num_cols // 2) - (block_width_in_cells // 2) - min_col
            else: # Fallback if shape is empty or malformed
                 self.current_block.col_offset = self.grid.num_cols // 2 - 2 # Default centering for 4-cell wide blocks

        else: # Fallback if cells[0] doesn't exist
            self.current_block.col_offset = self.grid.num_cols // 2 - 2


        self.current_block.row_offset = 0 
        
        if not self.current_block.is_valid_position(self.grid):
            self.active = False # Game over for this player
            play_sound("game_over")
            print(f"Player {self.player_id} game over on spawn.")

    def update_game_state(self, current_tick_time):
        if not self.active:
            return
        
        # Automatic block drop based on fall_speed_ms
        if current_tick_time - self.last_drop_event_time >= self.fall_speed_ms:
            self.attempt_drop_block()
            self.last_drop_event_time = current_tick_time
    
    def attempt_drop_block(self):
        if not self.active or not self.current_block:
            return False # Cannot drop if inactive or no block
        
        # Block.move returns True if successful, False if collision
        if not self.current_block.move(1, 0, self.grid): # Try to move 1 row down, 0 cols across
            self.lock_block_in_grid()
            return False # Block locked
        return True # Block moved successfully

    def attempt_move_horizontal(self, delta_col):
        if self.active and self.current_block:
            if self.current_block.move(0, delta_col, self.grid):
                play_sound("move")
                return True
        return False

    def attempt_rotate(self):
        if self.active and self.current_block:
            # Assuming Block.rotate handles its own validity checks
            # Block.rotate should return True on success, False on failure to rotate (e.g. collision)
            original_rotation_state = self.current_block.rotation_state
            self.current_block.rotate(self.grid) # Attempt rotation
            if self.current_block.rotation_state != original_rotation_state : # Check if rotation actually happened
                 play_sound("rotate") 
                 return True
            # If rotate method itself reverts and returns False, use that:
            # if self.current_block.rotate(self.grid): 
            #    play_sound("rotate")
            #    return True
        return False
            
    def perform_hard_drop(self):
        if not self.active or not self.current_block:
            return
        
        cells_dropped = 0
        while self.current_block.move(1, 0, self.grid):
            cells_dropped += 1
        self.score += cells_dropped * 1 # Small score for hard drop cells
        self.lock_block_in_grid()

    def process_continuous_inputs(self, current_tick_time, move_repeat_delay_ms):
        if not self.active or not self.current_block:
            return
        
        if current_tick_time - self.last_move_event_time > move_repeat_delay_ms:
            moved_this_tick = False
            if self.input_left_pressed:
                if self.attempt_move_horizontal(-1): moved_this_tick = True
            elif self.input_right_pressed:
                if self.attempt_move_horizontal(1): moved_this_tick = True
            
            if self.input_down_pressed: # Soft drop, can happen with horizontal
                if self.attempt_drop_block():
                    self.score += 1 # Score for soft drop
                    moved_this_tick = True # Reset timer for soft drop too
            
            if moved_this_tick:
                self.last_move_event_time = current_tick_time

    
    def lock_block_in_grid(self):
        if not self.current_block: return False
        
        self.grid.place_block(self.current_block) # from grid.py
        play_sound("drop")
        
        rows_cleared_now = self.grid.clear_rows() # from grid.py
        if rows_cleared_now > 0:
            play_sound("clear")
            self.lines_cleared_total += rows_cleared_now
            # Scoring: e.g., 1 line = 100, 2 = 300, 3 = 500, 4 = 800 (Tetris standard)
            # More complex scoring can be added here based on rows_cleared_now and self.level
            if rows_cleared_now == 1: self.score += 100 * self.level
            elif rows_cleared_now == 2: self.score += 300 * self.level
            elif rows_cleared_now == 3: self.score += 500 * self.level
            elif rows_cleared_now >= 4: self.score += 800 * self.level
            
            old_level = self.level
            self.level = min(10, (self.lines_cleared_total // 10) + 1) # Level up every 10 lines
            if self.level > old_level:
                play_sound("level_up")
            self.fall_speed_ms = LEVEL_SPEED[min(9, self.level - 1)]
        
        self.spawn_new_block() # Generate next piece
        return True

    def draw_player_game_field(self, surface, top_left_x, top_left_y):
        self.grid.draw(surface, top_left_x, top_left_y) # Grid handles its own drawing
        if self.active and self.current_block:
            self.current_block.draw(surface, top_left_x, top_left_y) # Block handles its own drawing relative to grid

    def draw_player_info_panel(self, surface, top_left_x, top_left_y, panel_width, panel_height):
        panel_rect = pygame.Rect(top_left_x, top_left_y, panel_width, panel_height)
        pygame.draw.rect(surface, LIGHT_GRAY, panel_rect) # Panel background
        pygame.draw.rect(surface, WHITE, panel_rect, 2) # Panel border

        current_y = top_left_y + INFO_PADDING

        # Player Title
        title_surf = self.font_panel_title.render(f"Player {self.player_id}", True, WHITE)
        title_rect = title_surf.get_rect(centerx=panel_rect.centerx, top=current_y)
        surface.blit(title_surf, title_rect)
        current_y += title_surf.get_height() + INFO_PADDING * 2

        # Score
        score_surf = self.font_panel_info.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_surf.get_rect(left=panel_rect.left + INFO_PADDING, top=current_y)
        surface.blit(score_surf, score_rect)
        current_y += score_surf.get_height() + INFO_PADDING

        # Level
        level_surf = self.font_panel_info.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_surf.get_rect(left=panel_rect.left + INFO_PADDING, top=current_y)
        surface.blit(level_surf, level_rect)
        current_y += level_surf.get_height() + INFO_PADDING * 2
        
        # Lines Cleared
        lines_surf = self.font_panel_info.render(f"Lines: {self.lines_cleared_total}", True, WHITE)
        lines_rect = lines_surf.get_rect(left=panel_rect.left + INFO_PADDING, top=current_y)
        surface.blit(lines_surf, lines_rect)
        current_y += lines_surf.get_height() + INFO_PADDING * 2


        # Next Piece Preview
        next_label_surf = self.font_panel_info.render("Next:", True, WHITE)
        next_label_rect = next_label_surf.get_rect(left=panel_rect.left + INFO_PADDING, top=current_y)
        surface.blit(next_label_surf, next_label_rect)
        current_y += next_label_surf.get_height() + INFO_PADDING // 2

        # Preview Box for Next Piece
        preview_box_size_cells = PREVIEW_SIZE # e.g., 4x4 cells
        preview_box_width_px = preview_box_size_cells * self.cell_size
        preview_box_height_px = preview_box_size_cells * self.cell_size 
        # Center preview box within the panel width if desired
        preview_box_x = panel_rect.left + (panel_width - preview_box_width_px) // 2
        preview_box_y = current_y
        
        pygame.draw.rect(surface, BLACK, (preview_box_x, preview_box_y, preview_box_width_px, preview_box_height_px)) # BG
        pygame.draw.rect(surface, WHITE, (preview_box_x, preview_box_y, preview_box_width_px, preview_box_height_px), 1) # Border

        if self.next_block:
            # Temporarily adjust next_block's offsets for drawing in the small preview
            original_row_offset = self.next_block.row_offset
            original_col_offset = self.next_block.col_offset

            # Get the actual cell data for the current rotation state of the next block
            # Ensure rotation_state is valid for self.next_block.cells
            current_rotation = self.next_block.rotation_state % len(self.next_block.cells)
            shape_to_draw = self.next_block.cells[current_rotation]
            
            min_r = 0; min_c = 0; max_r = 0; max_c = 0
            if shape_to_draw : # Check if shape_to_draw is not empty
                min_r = min(p.row for p in shape_to_draw)
                min_c = min(p.col for p in shape_to_draw)
                max_r = max(p.row for p in shape_to_draw)
                max_c = max(p.col for p in shape_to_draw)
            else: # Handle empty shape
                shape_to_draw = []


            shape_height_cells = max_r - min_r + 1 if shape_to_draw else 0
            shape_width_cells = max_c - min_c + 1 if shape_to_draw else 0

            cell_offset_x = (preview_box_size_cells - shape_width_cells) // 2
            cell_offset_y = (preview_box_size_cells - shape_height_cells) // 2
            
            for pos in shape_to_draw:
                draw_c = pos.col - min_c + cell_offset_x
                draw_r = pos.row - min_r + cell_offset_y
                
                if 0 <= draw_c < preview_box_size_cells and 0 <= draw_r < preview_box_size_cells:
                    rect = pygame.Rect(
                        preview_box_x + draw_c * self.cell_size + 1, 
                        preview_box_y + draw_r * self.cell_size + 1, 
                        self.cell_size -1, 
                        self.cell_size -1  
                    )
                    pygame.draw.rect(surface, self.next_block.color, rect)

            self.next_block.row_offset = original_row_offset
            self.next_block.col_offset = original_col_offset
        current_y += preview_box_height_px + INFO_PADDING * 2

        # Controls (static text for now)
        controls_title_surf = self.font_panel_info.render("Controls:", True, WHITE)
        controls_title_rect = controls_title_surf.get_rect(left=panel_rect.left + INFO_PADDING, top=current_y)
        surface.blit(controls_title_surf, controls_title_rect)
        current_y += controls_title_surf.get_height() + INFO_PADDING // 2

        control_texts = []
        if self.player_id == 1:
            control_texts = ["W: Rotate", "A: Left, D: Right", "S: Soft Drop", "Space: Hard Drop"]
        else: # Player 2
            control_texts = ["Up: Rotate", "Left, Right", "Down: Soft Drop", "Enter: Hard Drop"]
        
        for text in control_texts:
            control_surf = self.font_controls.render(text, True, WHITE)
            control_rect = control_surf.get_rect(left=panel_rect.left + INFO_PADDING, top=current_y)
            surface.blit(control_surf, control_rect)
            current_y += control_surf.get_height() + 2 


def draw_global_timer(surface, elapsed_ms, font, center_x, top_y):
    minutes = elapsed_ms // 60000
    seconds = (elapsed_ms % 60000) // 1000
    time_str = f"Time: {minutes:02d}:{seconds:02d}"
    timer_surf = font.render(time_str, True, WHITE)
    timer_rect = timer_surf.get_rect(centerx=center_x, top=top_y)
    surface.blit(timer_surf, timer_rect)


def show_multiplayer_end_screen(screen, winner_player_id, p1_score, p2_score, on_play_again, on_main_menu):
    font_title = pygame.font.SysFont("Arial", 60, bold=True)
    font_info = pygame.font.SysFont("Arial", 36)
    font_button = pygame.font.SysFont("Arial", 40)

    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    selected_option = 0 
    
    controller = None
    if pygame.joystick.get_count() > 0:
        try:
            controller = pygame.joystick.Joystick(0) 
            if not controller.get_init(): controller.init()
        except pygame.error: controller = None

    running_end_screen = True
    while running_end_screen:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_music()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    running_end_screen = False
                    on_main_menu()
                    return 
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    selected_option = 1 - selected_option
                    play_sound("menu_select")
                if event.key == pygame.K_RETURN:
                    play_sound("menu_select")
                    running_end_screen = False
                    if selected_option == 0: on_play_again()
                    else: on_main_menu()
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                play_again_button_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 + 20, 300, 60)
                main_menu_button_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 + 100, 300, 60)
                if play_again_button_rect.collidepoint(mouse_pos):
                    selected_option = 0 # Ensure correct option before action
                    play_sound("menu_select")
                    running_end_screen = False
                    on_play_again()
                    return
                elif main_menu_button_rect.collidepoint(mouse_pos):
                    selected_option = 1 # Ensure correct option
                    play_sound("menu_select")
                    running_end_screen = False
                    on_main_menu()
                    return

            if controller :
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = controller.get_hat(0)
                    if hat_y != 0: # Up or Down
                        selected_option = 1 - selected_option
                        play_sound("menu_select")
                if event.type == pygame.JOYBUTTONDOWN:
                    if controller.get_button(0): # A/X button
                        play_sound("menu_select")
                        running_end_screen = False
                        if selected_option == 0: on_play_again()
                        else: on_main_menu()
                        return


        screen.fill(GRAY) 

        winner_text_str = f"Player {winner_player_id} Wins!" if winner_player_id else "It's a Tie!"
        title_surf = font_title.render(winner_text_str, True, WHITE)
        title_rect = title_surf.get_rect(center=(screen_width // 2, screen_height // 4))
        screen.blit(title_surf, title_rect)

        p1_score_surf = font_info.render(f"Player 1 Score: {p1_score}", True, WHITE)
        p1_score_rect = p1_score_surf.get_rect(center=(screen_width // 2, title_rect.bottom + 50))
        screen.blit(p1_score_surf, p1_score_rect)

        p2_score_surf = font_info.render(f"Player 2 Score: {p2_score}", True, WHITE)
        p2_score_rect = p2_score_surf.get_rect(center=(screen_width // 2, p1_score_rect.bottom + 20))
        screen.blit(p2_score_surf, p2_score_rect)

        play_again_color = RED if selected_option == 0 else WHITE
        main_menu_color = RED if selected_option == 1 else WHITE

        # Define button rects for drawing and collision (already done for mouse)
        play_again_button_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 + 20, 300, 60)
        main_menu_button_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 + 100, 300, 60)

        # Draw button backgrounds
        pygame.draw.rect(screen, LIGHT_GRAY if selected_option == 0 else GRAY, play_again_button_rect, border_radius=10)
        pygame.draw.rect(screen, LIGHT_GRAY if selected_option == 1 else GRAY, main_menu_button_rect, border_radius=10)
        
        # Draw button text
        play_again_surf = font_button.render("Play Again", True, play_again_color)
        play_again_text_rect = play_again_surf.get_rect(center=play_again_button_rect.center)
        screen.blit(play_again_surf, play_again_text_rect)

        main_menu_surf = font_button.render("Main Menu", True, main_menu_color)
        main_menu_text_rect = main_menu_surf.get_rect(center=main_menu_button_rect.center)
        screen.blit(main_menu_surf, main_menu_text_rect)


        pygame.display.flip()
        pygame.time.Clock().tick(30)


def multiplayer_mode(): # Renamed from multiplayer_game_loop
    pygame.init()
    if not pygame.mixer.get_init(): pygame.mixer.init()
    load_game_sounds()
    
    est_panel_content_height = (28 + INFO_PADDING + 
                                22 + INFO_PADDING + 
                                22 + INFO_PADDING + 
                                22 + INFO_PADDING + 
                                22 + INFO_PADDING + 
                                (PREVIEW_SIZE * CELL_SIZE) + INFO_PADDING + 
                                22 + INFO_PADDING + 
                                (16 * 4) + INFO_PADDING * 2) # Increased to 4 lines for controls
    
    window_height = OUTER_MARGIN_VERTICAL * 2 + max(GAME_FIELD_HEIGHT_PX, est_panel_content_height)
    window_width = (OUTER_MARGIN_HORIZONTAL * 2 + 
                    GAME_FIELD_WIDTH_PX * 2 +  
                    PANEL_INFO_WIDTH * 2 +     
                    FIELD_MARGIN_HORIZONTAL)   
    
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Tetris - Multiplayer")

    player1 = MultiplayerPlayer(1)
    player2 = MultiplayerPlayer(2)
    
    clock = pygame.time.Clock()
    game_running = True
    continuous_move_delay_ms = 120 

    p1_field_x = OUTER_MARGIN_HORIZONTAL
    p1_field_y = OUTER_MARGIN_VERTICAL + 30 
    p1_panel_x = p1_field_x + GAME_FIELD_WIDTH_PX + INFO_PADDING 

    p2_field_x = p1_panel_x + PANEL_INFO_WIDTH + FIELD_MARGIN_HORIZONTAL
    p2_field_y = p1_field_y 
    p2_panel_x = p2_field_x + GAME_FIELD_WIDTH_PX + INFO_PADDING

    panel_common_y = p1_field_y
    panel_common_height = window_height - OUTER_MARGIN_VERTICAL * 2 - 30 

    global_timer_font = pygame.font.SysFont("Arial", 24, bold=True)
    game_start_time = pygame.time.get_ticks()


    p1_controller = None
    p2_controller = None
    joystick_count = pygame.joystick.get_count()
    if joystick_count > 0:
        try:
            p1_controller = pygame.joystick.Joystick(0)
            if not p1_controller.get_init(): p1_controller.init()
        except pygame.error: p1_controller = None
    if joystick_count > 1:
        try:
            p2_controller = pygame.joystick.Joystick(1)
            if not p2_controller.get_init(): p2_controller.init()
        except pygame.error: p2_controller = None


    play_music() 

    while game_running:
        current_tick = pygame.time.get_ticks()
        ensure_music_playing() 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_running = False 

            # --- Player 1 Input (Keyboard) ---
            if player1.active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a: player1.input_left_pressed = True; player1.attempt_move_horizontal(-1); player1.last_move_event_time = current_tick
                    elif event.key == pygame.K_d: player1.input_right_pressed = True; player1.attempt_move_horizontal(1); player1.last_move_event_time = current_tick
                    elif event.key == pygame.K_s: player1.input_down_pressed = True; # Set flag, continuous handler will do action
                    elif event.key == pygame.K_w: player1.attempt_rotate()
                    elif event.key == pygame.K_SPACE: player1.perform_hard_drop()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_a: player1.input_left_pressed = False
                    elif event.key == pygame.K_d: player1.input_right_pressed = False
                    elif event.key == pygame.K_s: player1.input_down_pressed = False
            
            # --- Player 1 Input (Controller) ---
            if player1.active and p1_controller:
                if event.type == pygame.JOYBUTTONDOWN and event.instance_id == p1_controller.get_instance_id():
                    if event.button == 3: player1.attempt_rotate() 
                    elif event.button == 0: player1.perform_hard_drop() 
                if event.type == pygame.JOYHATMOTION and event.instance_id == p1_controller.get_instance_id():
                    hat_x, hat_y = event.value
                    player1.input_left_pressed = (hat_x == -1)
                    player1.input_right_pressed = (hat_x == 1)
                    player1.input_down_pressed = (hat_y == -1)
                    if hat_x !=0 or hat_y !=0 : player1.last_move_event_time = current_tick # Reset for new D-pad input
                # Add JOYAXISMOTION if needed, similar to JOYHATMOTION for analog sticks


            # --- Player 2 Input (Keyboard) ---
            if player2.active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT: player2.input_left_pressed = True; player2.attempt_move_horizontal(-1); player2.last_move_event_time = current_tick
                    elif event.key == pygame.K_RIGHT: player2.input_right_pressed = True; player2.attempt_move_horizontal(1); player2.last_move_event_time = current_tick
                    elif event.key == pygame.K_DOWN: player2.input_down_pressed = True; 
                    elif event.key == pygame.K_UP: player2.attempt_rotate()
                    elif event.key == pygame.K_RETURN: player2.perform_hard_drop() 
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT: player2.input_left_pressed = False
                    elif event.key == pygame.K_RIGHT: player2.input_right_pressed = False
                    elif event.key == pygame.K_DOWN: player2.input_down_pressed = False

            # --- Player 2 Input (Controller) ---
            if player2.active and p2_controller:
                if event.type == pygame.JOYBUTTONDOWN and event.instance_id == p2_controller.get_instance_id():
                    if event.button == 3: player2.attempt_rotate() 
                    elif event.button == 0: player2.perform_hard_drop()
                if event.type == pygame.JOYHATMOTION and event.instance_id == p2_controller.get_instance_id():
                    hat_x, hat_y = event.value
                    player2.input_left_pressed = (hat_x == -1)
                    player2.input_right_pressed = (hat_x == 1)
                    player2.input_down_pressed = (hat_y == -1)
                    if hat_x !=0 or hat_y !=0 : player2.last_move_event_time = current_tick


        if player1.active:
            player1.update_game_state(current_tick)
            player1.process_continuous_inputs(current_tick, continuous_move_delay_ms)
        if player2.active:
            player2.update_game_state(current_tick)
            player2.process_continuous_inputs(current_tick, continuous_move_delay_ms)

        screen.fill(GRAY) 

        player1.draw_player_game_field(screen, p1_field_x, p1_field_y)
        player1.draw_player_info_panel(screen, p1_panel_x, panel_common_y, PANEL_INFO_WIDTH, panel_common_height)

        player2.draw_player_game_field(screen, p2_field_x, p2_field_y)
        player2.draw_player_info_panel(screen, p2_panel_x, panel_common_y, PANEL_INFO_WIDTH, panel_common_height)
        
        elapsed_time = current_tick - game_start_time
        draw_global_timer(screen, elapsed_time, global_timer_font, window_width // 2, OUTER_MARGIN_VERTICAL // 2)


        if not player1.active or not player2.active:
            game_running = False 
            winner_id = None
            if player1.active and not player2.active: winner_id = 1
            elif player2.active and not player1.active: winner_id = 2
            elif not player1.active and not player2.active:
                if player1.score > player2.score: winner_id = 1
                elif player2.score > player1.score: winner_id = 2
                else: winner_id = None 

            stop_music() 
            
            def play_again_action():
                multiplayer_mode() # Call the renamed function
            
            def main_menu_action():
                # This is tricky. Ideally main.py's main_menu() is called.
                # For now, this function will simply allow the loop to terminate.
                # The calling code in main.py (start_multiplayer) will then call main_menu().
                print("Multiplayer ended. Returning to main menu via main.py...")


            show_multiplayer_end_screen(screen, winner_id, player1.score, player2.score, 
                                        on_play_again=play_again_action, 
                                        on_main_menu=main_menu_action)
            return 


        pygame.display.flip()
        clock.tick(60) 

    stop_music()
    # When game_running becomes false due to ESCAPE or QUIT, this point is reached.
    # The main_menu() call is handled by main.py after this function returns.


if __name__ == '__main__':
    multiplayer_mode() # Call the renamed function
    pygame.quit()
    sys.exit()