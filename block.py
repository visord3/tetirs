import pygame
class Block:
    """
    Base class for all Tetris blocks.

    - `id`: A unique integer to store in the Grid (1..7).
    - `color`: RGB tuple for drawing.
    - `cells`: A dict { rotation_state: [Position, Position, ...] }
    - `row_offset`, `col_offset`: Current top-left position on the grid.
    - `rotation_state`: Which "orientation" is currently active (0..3).
    """

    def __init__(self, block_id, color, cell_size=30):
        self.id = block_id
        self.color = color
        self.cell_size = cell_size

        # Dictionary of rotation states -> list of Position objects
        self.cells = {}

        # Block’s position on the grid
        self.row_offset = 0
        self.col_offset = 0

        # 0, 1, 2, 3 for the 4 possible rotations (some blocks only need 2 or 1)
        self.rotation_state = 0

    def move(self, drow, dcol, grid):
        """
        Attempt to move the block by (drow, dcol).
        Returns True if move is valid; False if it had to revert.
        """
        original_row_offset = self.row_offset
        original_col_offset = self.col_offset

        self.row_offset += drow
        self.col_offset += dcol

        if not self.is_valid_position(grid):
            # Revert if invalid
            self.row_offset = original_row_offset
            self.col_offset = original_col_offset
            return False

        return True

    def rotate(self, grid):
        """
        Attempt to rotate the block to the next state.
        Revert if invalid.
        """
        old_state = self.rotation_state
        self.rotation_state = (self.rotation_state + 1) % len(self.cells)

        if not self.is_valid_position(grid):
            # Revert rotation if invalid
            self.rotation_state = old_state

    def get_cell_positions(self):
        """
        Returns a list of (row, col) for the current rotation and offsets.
        """
        shape_positions = self.cells[self.rotation_state]
        return [
            (p.row + self.row_offset, p.col + self.col_offset)
            for p in shape_positions
        ]

    def is_valid_position(self, grid):
        """
        Checks if all the block’s cells are:
          1) Inside the grid boundaries,
          2) Not colliding with existing blocks.
        """
        for (r, c) in self.get_cell_positions():
            # Check out-of-bounds
            if r < 0 or r >= grid.num_rows or c < 0 or c >= grid.num_cols:
                return False
            # Check collision
            if grid.grid[r][c] != 0:
                return False
        return True

    def draw(self, surface, offset_x=0, offset_y=0):
        """
        Draw the block with the given offsets.
        """
        for (r, c) in self.get_cell_positions():
            rect = pygame.Rect(
                offset_x + c * self.cell_size + 1,
                offset_y + r * self.cell_size + 1,
                self.cell_size - 1,
                self.cell_size - 1
            )
            pygame.draw.rect(surface, self.color, rect)
