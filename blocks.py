from block import Block
from position import Position

class IBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(1, (0, 255, 255), cell_size)
        # Define the rotation states
        # The I-block is a 4x1 line. We'll define each rotation.
        self.cells = {
            0: [Position(0, 0), Position(0, 1), Position(0, 2), Position(0, 3)],
            1: [Position(0, 0), Position(1, 0), Position(2, 0), Position(3, 0)],
        }
        # Some shapes only need 2 states, but let's store them up to 4
        # by repeating for safe usage of modulo.
        self.cells[2] = self.cells[0]
        self.cells[3] = self.cells[1]


class OBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(2, (255, 255, 0), cell_size)
        # 2x2 square. All rotations are the same.
        self.cells = {
            0: [Position(0, 0), Position(0, 1), Position(1, 0), Position(1, 1)],
            1: [Position(0, 0), Position(0, 1), Position(1, 0), Position(1, 1)],
            2: [Position(0, 0), Position(0, 1), Position(1, 0), Position(1, 1)],
            3: [Position(0, 0), Position(0, 1), Position(1, 0), Position(1, 1)],
        }


class TBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(3, (128, 0, 128), cell_size)
        self.cells = {
            0: [Position(0, 0), Position(0, 1), Position(0, 2), Position(1, 1)],
            1: [Position(0, 1), Position(1, 1), Position(2, 1), Position(1, 0)],
            2: [Position(1, 0), Position(1, 1), Position(1, 2), Position(0, 1)],
            3: [Position(0, 0), Position(1, 0), Position(2, 0), Position(1, 1)],
        }


class SBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(4, (0, 255, 0), cell_size)
        self.cells = {
            0: [Position(0, 1), Position(0, 2), Position(1, 0), Position(1, 1)],
            1: [Position(0, 0), Position(1, 0), Position(1, 1), Position(2, 1)],
            2: [Position(0, 1), Position(0, 2), Position(1, 0), Position(1, 1)],
            3: [Position(0, 0), Position(1, 0), Position(1, 1), Position(2, 1)],
        }


class ZBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(5, (255, 0, 0), cell_size)
        self.cells = {
            0: [Position(0, 0), Position(0, 1), Position(1, 1), Position(1, 2)],
            1: [Position(0, 1), Position(1, 0), Position(1, 1), Position(2, 0)],
            2: [Position(0, 0), Position(0, 1), Position(1, 1), Position(1, 2)],
            3: [Position(0, 1), Position(1, 0), Position(1, 1), Position(2, 0)],
        }


class JBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(6, (0, 0, 255), cell_size)
        self.cells = {
            0: [Position(0, 0), Position(1, 0), Position(1, 1), Position(1, 2)],
            1: [Position(0, 0), Position(0, 1), Position(1, 0), Position(2, 0)],
            2: [Position(0, 0), Position(0, 1), Position(0, 2), Position(1, 2)],
            3: [Position(0, 1), Position(1, 1), Position(2, 0), Position(2, 1)],
        }


class LBlock(Block):
    def __init__(self, cell_size=30):
        super().__init__(7, (255, 140, 0), cell_size)
        self.cells = {
            0: [Position(0, 2), Position(1, 0), Position(1, 1), Position(1, 2)],
            1: [Position(0, 0), Position(1, 0), Position(2, 0), Position(2, 1)],
            2: [Position(0, 0), Position(0, 1), Position(0, 2), Position(1, 0)],
            3: [Position(0, 0), Position(1, 0), Position(2, 0), Position(0, 1)],
        }