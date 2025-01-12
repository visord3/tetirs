# main.py
import sys
import pygame
from single_player import single_player_mode
from multiplayer import multiplayer_mode

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris Menu")
font = pygame.font.SysFont("Arial", 36)

def main_menu():
    running = True
    while running:
        screen.fill(GRAY)

        # Title
        title_text = font.render("TETRIS GAME", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_text, title_rect)

        # Single Player button
        single_player_button = pygame.Rect(150, 200, 300, 50)
        pygame.draw.rect(screen, WHITE, single_player_button)
        single_text = font.render("Single Player", True, BLACK)
        single_rect = single_text.get_rect(center=single_player_button.center)
        screen.blit(single_text, single_rect)

        # Multiplayer button
        multiplayer_button = pygame.Rect(150, 300, 300, 50)
        pygame.draw.rect(screen, WHITE, multiplayer_button)
        multi_text = font.render("Multiplayer", True, BLACK)
        multi_rect = multi_text.get_rect(center=multiplayer_button.center)
        screen.blit(multi_text, multi_rect)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if single_player_button.collidepoint(event.pos):
                    single_player_mode()
                elif multiplayer_button.collidepoint(event.pos):
                    multiplayer_mode()

        pygame.display.flip()

def main():
    main_menu()

if __name__ == "__main__":
    main()
