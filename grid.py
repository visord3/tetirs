import  pygame
import random
from colors import Colors
class Grid:
    def __init__(self, num_cols, num_rows, cell_size):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.cell_size = cell_size

        # Create a 2D grid filled with zeros
        self.grid = [
            [0 for _ in range(self.num_cols)]
            for _ in range(self.num_rows)
        ]

        # Get cell colors from your Colors class
        self.colors = Colors.get_cell_colors()

    def draw(self, screen, offset_x=0, offset_y=0):
        """
        Draw each cell in the grid, applying offset_x and offset_y.
        Also draw a white border and faint grid lines for empty cells.
        """
        for row in range(self.num_rows):
            for col in range(self.num_cols):
                cell_value = self.grid[row][col]
                # Use colors from the Colors class
                if cell_value == 0:
                    color = (30, 30, 30)  # Faint gray for empty cells
                else:
                    color = self.colors[min(cell_value, len(self.colors) - 1)]
                cell_rect = pygame.Rect(
                    offset_x + col * self.cell_size,
                    offset_y + row * self.cell_size,
                    self.cell_size - 1,
                    self.cell_size - 1
                )
                pygame.draw.rect(screen, color, cell_rect)
                # Draw faint grid lines for all cells
                pygame.draw.rect(screen, (60, 60, 60), cell_rect, 1)
        # Draw a white border around the grid
        border_rect = pygame.Rect(
            offset_x, offset_y,
            self.num_cols * self.cell_size, self.num_rows * self.cell_size
        )
        pygame.draw.rect(screen, (255, 255, 255), border_rect, 2)

    def place_block(self, block):
        """
        Lock the block's cells into the grid (store its ID).
        """
        for (row, col) in block.get_cell_positions():
            if 0 <= row < self.num_rows and 0 <= col < self.num_cols:
                self.grid[row][col] = block.id

    def clear_rows(self):
        """
        Clears any fully filled rows and returns the count of cleared rows.
        """
        cleared_rows = 0
        # We'll check row by row.
        for row in range(self.num_rows):
            # If none of the cells in this row are 0, it's fully filled
            if all(self.grid[row]):
                del self.grid[row]
                self.grid.insert(0, [0 for _ in range(self.num_cols)])
                cleared_rows += 1
        return cleared_rows