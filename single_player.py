# single_player.py
import pygame
import random
from grid import Grid
from blocks import JBlock, LBlock, SBlock, ZBlock, IBlock, OBlock, TBlock

pygame.mixer.init()
pygame.mixer.music.load("tetris_music/tetris music.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.load("tetris_music/clear.wav")
pygame.mixer.music.set_volume(1.0)




line_clear_sfx = pygame.mixer.Sound("tetris_music/clear.wav")
line_clear_sfx.set_volume(1.0)

# List of possible blocks
block_types = [JBlock, LBlock, SBlock, ZBlock, IBlock, OBlock, TBlock]

def adjust_fall_speed(lines_cleared):
    """
    Return the drop speed in milliseconds (lower = faster).
    Start at 500ms, and speed up by 10ms every 10 lines, down to a minimum of 100ms.
    """
    return max(100, 500 - (lines_cleared // 10) * 10)

def get_line_clear_score(lines_cleared):
    """
    Return the score for number of lines cleared at once.
    Also play the line clear sound if lines_cleared > 0.
    """
    if lines_cleared > 0:
        line_clear_sfx.play()
    if lines_cleared == 1:
        return 100
    elif lines_cleared == 2:
        return 300
    elif lines_cleared == 3:
        return 500
    elif lines_cleared == 4:
        return 800
    return 0

def spawn_block(game_grid):
    """
    Spawn a new random block. If it doesn't fit at row=0 (collision),
    return None -> game over.
    """
    block = random.choice(block_types)(cell_size=game_grid.cell_size)
    # Start in the middle
    block.col_offset = game_grid.num_cols // 2 - 1
    block.row_offset = 0
    # If invalid right away, game over
    if not block.is_valid_position(game_grid):
        return None
    return block

def single_player_mode():
    SCREEN_WIDTH = 300
    SCREEN_HEIGHT = 600
    CELL_SIZE = 30

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Single Player Tetris")

    grid = Grid(num_cols=10, num_rows=20, cell_size=CELL_SIZE)

    clock = pygame.time.Clock()
    running = True
    score = 0
    total_lines = 0

    block = spawn_block(grid)
    if not block:
        print("Game Over immediately!")
        return

    fall_speed = adjust_fall_speed(total_lines)  # ms
    last_drop_time = pygame.time.get_ticks()

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and block:
                if event.key == pygame.K_LEFT:
                    # Move left if valid
                    block.move(0, -1, grid)
                elif event.key == pygame.K_RIGHT:
                    # Move right if valid
                    block.move(0, 1, grid)
                elif event.key == pygame.K_DOWN:
                    # Soft drop: try to move down
                    if not block.move(1, 0, grid):
                        # Can't move -> lock
                        grid.place_block(block)
                        lines_cleared = grid.clear_rows()
                        if lines_cleared:
                            total_lines += lines_cleared
                            score += get_line_clear_score(lines_cleared)
                            fall_speed = adjust_fall_speed(total_lines)
                        block = spawn_block(grid)
                        if not block:
                            print("Game Over!")
                            running = False
                elif event.key == pygame.K_UP:
                    # Rotate
                    block.rotate(grid)

        # Timed auto-drop
        if block and (now - last_drop_time >= fall_speed):
            if not block.move(1, 0, grid):
                # Lock block
                grid.place_block(block)
                lines_cleared = grid.clear_rows()
                if lines_cleared:
                    total_lines += lines_cleared
                    score += get_line_clear_score(lines_cleared)
                    fall_speed = adjust_fall_speed(total_lines)

                block = spawn_block(grid)
                if not block:
                    print("Game Over!")
                    running = False

            last_drop_time = now

        screen.fill((0, 0, 0))
        grid.draw(screen)
        if block:
            block.draw(screen)

        font = pygame.font.SysFont("Arial", 24)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
