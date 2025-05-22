import pygame
from constants import *

class Player:
    def __init__(self):
        self.field = [[0]*PLAYFIELD_W for _ in range(PLAYFIELD_H)]
        self.next_piece = [(1,1), (2,1), (1,2), (2,2)]  # Example: O block
        self.score = 0
        self.level = 1

    def draw_playfield(self, surf, x, y):
        pygame.draw.rect(surf, (0,0,0), (x, y, FIELD_PIX_W, FIELD_PIX_H))
        pygame.draw.rect(surf, (255,255,255), (x, y, FIELD_PIX_W, FIELD_PIX_H), 2)
        for row in range(PLAYFIELD_H):
            for col in range(PLAYFIELD_W):
                val = self.field[row][col]
                if val:
                    pygame.draw.rect(
                        surf, val,
                        (x + col*CELL_SIZE, y + row*CELL_SIZE, CELL_SIZE-1, CELL_SIZE-1)
                    )

    def draw_score_panel(self, surf, x, y, score, level):
        panel_h = 3*CELL_SIZE + PADDING*2
        pygame.draw.rect(surf, (180,180,180), (x, y, INFO_PIX_W, panel_h))
        pygame.draw.rect(surf, (255,255,255), (x, y, INFO_PIX_W, panel_h), 2)
        font = pygame.font.SysFont("Arial", 22, bold=True)
        surf.blit(font.render("Score", True, (0,0,0)), (x+PADDING, y+PADDING))
        surf.blit(font.render(str(score), True, (0,0,0)), (x+PADDING, y+PADDING+CELL_SIZE))
        surf.blit(font.render("Level", True, (0,0,0)), (x+INFO_PIX_W//2, y+PADDING))
        surf.blit(font.render(str(level), True, (0,0,0)), (x+INFO_PIX_W//2, y+PADDING+CELL_SIZE))

    def draw_next_piece(self, surf, x, y):
        font = pygame.font.SysFont("Arial", 20, bold=True)
        surf.blit(font.render("Next:", True, (0,0,0)), (x, y))
        box_y = y + font.get_height() + PADDING
        box_size = 4 * CELL_SIZE
        pygame.draw.rect(surf, (120,120,120), (x, box_y, box_size, box_size))
        pygame.draw.rect(surf, (255,255,255), (x, box_y, box_size, box_size), 2)
        if self.next_piece:
            piece = self.next_piece
            min_x = min(px for px,py in piece)
            min_y = min(py for px,py in piece)
            max_x = max(px for px,py in piece)
            max_y = max(py for px,py in piece)
            offset_x = (4 - (max_x-min_x+1))//2
            offset_y = (4 - (max_y-min_y+1))//2
            for px, py in piece:
                pygame.draw.rect(
                    surf, (0,255,0),
                    (x + (px-min_x+offset_x)*CELL_SIZE, box_y + (py-min_y+offset_y)*CELL_SIZE, CELL_SIZE-2, CELL_SIZE-2)
                ) 