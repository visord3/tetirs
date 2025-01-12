# multiplayer.py
import sys
import pygame
import random

from grid import Grid
from blocks import JBlock, LBlock, SBlock, ZBlock, IBlock, OBlock, TBlock
from single_player import spawn_block, adjust_fall_speed, get_line_clear_score

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

    while running:
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
        pygame.draw.rect(screen, (255, 255, 255), play_again_button)
        play_again_text = font.render("Play Again", True, (0, 0, 0))
        play_again_rect = play_again_text.get_rect(center=play_again_button.center)
        screen.blit(play_again_text, play_again_rect)

        # Quit button
        quit_button = pygame.Rect(150, 400, 300, 50)
        pygame.draw.rect(screen, (255, 255, 255), quit_button)
        quit_text = font.render("Quit", True, (0, 0, 0))
        quit_rect = quit_text.get_rect(center=quit_button.center)
        screen.blit(quit_text, quit_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_button.collidepoint(event.pos):
                    return True  # "Play Again"
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    return False

#########################
# MULTIPLAYER MODE
#########################
def multiplayer_mode():
    SCREEN_WIDTH = 600
    SCREEN_HEIGHT = 600
    CELL_SIZE = 30

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multiplayer Tetris")

    clock = pygame.time.Clock()
    running = True

    # Create the two 10x20 grids
    player1_grid = Grid(10, 20, CELL_SIZE)
    player2_grid = Grid(10, 20, CELL_SIZE)

    score_p1 = 0
    score_p2 = 0
    total_lines_p1 = 0
    total_lines_p2 = 0

    # Game duration in seconds
    timer = 60
    start_ticks = pygame.time.get_ticks()

    # Spawn initial blocks for both players
    block_p1 = spawn_block(player1_grid)
    block_p2 = spawn_block(player2_grid)

    # Fall speeds and last drop times for each player
    fall_speed_p1 = adjust_fall_speed(total_lines_p1)  # ms
    fall_speed_p2 = adjust_fall_speed(total_lines_p2)  # ms
    last_drop_time_p1 = pygame.time.get_ticks()
    last_drop_time_p2 = pygame.time.get_ticks()

    while running:
        now = pygame.time.get_ticks()
        elapsed_time = (now - start_ticks) // 1000
        remaining_time = timer - elapsed_time
        if remaining_time <= 0:
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                ###############
                # Player 1
                ###############
                if block_p1:
                    if event.key == pygame.K_LEFT:
                        # Move left
                        block_p1.col_offset -= 1
                        if not block_p1.is_valid_position(player1_grid):
                            block_p1.col_offset += 1
                    elif event.key == pygame.K_RIGHT:
                        # Move right
                        block_p1.col_offset += 1
                        if not block_p1.is_valid_position(player1_grid):
                            block_p1.col_offset -= 1
                    elif event.key == pygame.K_DOWN:
                        # Soft drop
                        block_p1.row_offset += 1
                        if not block_p1.is_valid_position(player1_grid):
                            # Revert
                            block_p1.row_offset -= 1
                            # Lock block
                            player1_grid.place_block(block_p1)
                            lines_cleared = player1_grid.clear_rows()
                            if lines_cleared:
                                total_lines_p1 += lines_cleared
                                score_p1 += get_line_clear_score(lines_cleared)
                                fall_speed_p1 = adjust_fall_speed(total_lines_p1)

                            block_p1 = spawn_block(player1_grid)
                            if not block_p1:
                                running = False
                    elif event.key == pygame.K_UP:
                        # Rotate
                        block_p1.rotate(player1_grid)

                ###############
                # Player 2
                ###############
                if block_p2:
                    if event.key == pygame.K_a:
                        block_p2.col_offset -= 1
                        if not block_p2.is_valid_position(player2_grid):
                            block_p2.col_offset += 1
                    elif event.key == pygame.K_d:
                        block_p2.col_offset += 1
                        if not block_p2.is_valid_position(player2_grid):
                            block_p2.col_offset -= 1
                    elif event.key == pygame.K_s:
                        block_p2.row_offset += 1
                        if not block_p2.is_valid_position(player2_grid):
                            block_p2.row_offset -= 1
                            # Lock block
                            player2_grid.place_block(block_p2)
                            lines_cleared = player2_grid.clear_rows()
                            if lines_cleared:
                                total_lines_p2 += lines_cleared
                                score_p2 += get_line_clear_score(lines_cleared)
                                fall_speed_p2 = adjust_fall_speed(total_lines_p2)

                            block_p2 = spawn_block(player2_grid)
                            if not block_p2:
                                running = False
                    elif event.key == pygame.K_w:
                        block_p2.rotate(player2_grid)

        ######################
        # Timed auto-drop for P1
        ######################
        if block_p1 and (now - last_drop_time_p1 >= fall_speed_p1):
            block_p1.row_offset += 1
            if not block_p1.is_valid_position(player1_grid):
                block_p1.row_offset -= 1
                player1_grid.place_block(block_p1)
                lines_cleared = player1_grid.clear_rows()
                if lines_cleared:
                    total_lines_p1 += lines_cleared
                    score_p1 += get_line_clear_score(lines_cleared)
                    fall_speed_p1 = adjust_fall_speed(total_lines_p1)

                block_p1 = spawn_block(player1_grid)
                if not block_p1:
                    running = False
            last_drop_time_p1 = now

        ######################
        # Timed auto-drop for P2
        ######################
        if block_p2 and (now - last_drop_time_p2 >= fall_speed_p2):
            block_p2.row_offset += 1
            if not block_p2.is_valid_position(player2_grid):
                block_p2.row_offset -= 1
                player2_grid.place_block(block_p2)
                lines_cleared = player2_grid.clear_rows()
                if lines_cleared:
                    total_lines_p2 += lines_cleared
                    score_p2 += get_line_clear_score(lines_cleared)
                    fall_speed_p2 = adjust_fall_speed(total_lines_p2)

                block_p2 = spawn_block(player2_grid)
                if not block_p2:
                    running = False
            last_drop_time_p2 = now

        #########################
        # DRAWING
        #########################
        screen.fill((0, 0, 0))

        # Draw each grid
        player1_grid.draw(screen, offset_x=0, offset_y=0)
        player2_grid.draw(screen, offset_x=SCREEN_WIDTH // 2, offset_y=0)

        # Draw the vertical dividing line in the middle
        pygame.draw.line(
            screen,
            (255, 255, 255),               # white
            (SCREEN_WIDTH // 2, 0),        # start at top center
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT),  # down to bottom center
            2                              # line thickness
        )

        # Draw blocks
        if block_p1:
            block_p1.draw(screen, offset_x=0, offset_y=0)
        if block_p2:
            block_p2.draw(screen, offset_x=SCREEN_WIDTH // 2, offset_y=0)

        # Draw scores and timer
        font = pygame.font.SysFont("Arial", 24)
        score_text_p1 = font.render(f"P1 Score: {score_p1}", True, (255, 255, 255))
        score_text_p2 = font.render(f"P2 Score: {score_p2}", True, (255, 255, 255))
        timer_text = font.render(f"Time: {remaining_time}", True, (255, 255, 255))
        screen.blit(score_text_p1, (10, 10))
        screen.blit(score_text_p2, (SCREEN_WIDTH // 2 + 10, 10))
        screen.blit(timer_text, (SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT - 30))

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
    else:
        pygame.quit()
        sys.exit()
