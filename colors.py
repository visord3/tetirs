class Colors:
    @staticmethod
    def get_cell_colors():
        # Colors for each block type, indexed by their IDs
        return [
            (0, 0, 0),       # Color for empty cells (e.g., black)
            (255, 0, 0),     # Block type 1 (red)
            (0, 255, 0),     # Block type 2 (green)
            (0, 0, 255),     # Block type 3 (blue)
            (255, 255, 0),   # Block type 4 (yellow)
            (255, 165, 0),   # Block type 5 (orange)
            (128, 0, 128),   # Block type 6 (purple)
            (0, 255, 255),   # Block type 7 (cyan)
        ]
