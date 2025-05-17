import sys
import pygame
import os

# Import game modes
from single_player import SinglePlayerGame
from multiplayer import multiplayer_mode

# Initialize pygame
pygame.init()
pygame.mixer.init()
pygame.joystick.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
HIGHLIGHT = (100, 100, 255)
TITLE_COLOR = (255, 255, 100)

# Setup display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")

# Fonts
title_font = pygame.font.SysFont("Arial", 72, bold=True)
menu_font = pygame.font.SysFont("Arial", 48)
info_font = pygame.font.SysFont("Arial", 24)

# Controller setup
controller = None


def initialize_controller():
    """Initialize and return PS5 controller if available"""
    global controller

    # Reset joystick module to detect newly connected controllers
    pygame.joystick.quit()
    pygame.joystick.init()

    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
        print(f"Controller connected: {controller.get_name()}")
        return controller
    else:
        print("No controller connected")
        controller = None
        return None


def main_menu():
    """Main menu with controller support"""
    global controller

    # Background music (optional)
    # pygame.mixer.music.load("menu_music.mp3")
    # pygame.mixer.music.play(-1)  # Loop infinitely

    # Initialize controller
    controller = initialize_controller()

    # Menu options and state
    menu_options = ["Single Player", "Multiplayer", "Quit"]
    selected_option = 0
    button_cooldown = 0
    cooldown_time = 200  # milliseconds

    clock = pygame.time.Clock()
    running = True

    while running:
        # Delta time for consistent animations
        dt = clock.tick(60)

        # Reduce button cooldown
        if button_cooldown > 0:
            button_cooldown -= dt

        # Check for controller reconnection if none is connected
        if controller is None and pygame.time.get_ticks() % 3000 < 50:  # Check every 3 seconds
            controller = initialize_controller()

        # Clear screen
        screen.fill(GRAY)

        # Draw title
        title_text = title_font.render("TETRIS", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title_text, title_rect)

        # Draw menu options
        for i, option in enumerate(menu_options):
            color = HIGHLIGHT if i == selected_option else WHITE
            text = menu_font.render(option, True, color)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 80))
            screen.blit(text, rect)

        # Draw controller status
        if controller:
            status_text = info_font.render(f"Controller connected: {controller.get_name()}", True, WHITE)
        else:
            status_text = info_font.render("No controller connected. Using keyboard controls.", True, WHITE)
        screen.blit(status_text, (20, SCREEN_HEIGHT - 30))

        # Draw controls info
        if controller:
            controls_text = info_font.render("D-pad or Left Stick to navigate, X button to select", True, WHITE)
        else:
            controls_text = info_font.render("Arrow keys to navigate, Enter to select", True, WHITE)
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        screen.blit(controls_text, controls_rect)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Keyboard controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if button_cooldown <= 0:
                        selected_option = (selected_option - 1) % len(menu_options)
                        button_cooldown = cooldown_time
                elif event.key == pygame.K_DOWN:
                    if button_cooldown <= 0:
                        selected_option = (selected_option + 1) % len(menu_options)
                        button_cooldown = cooldown_time
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:  # Single Player
                        # Start single player game
                        game = SinglePlayerGame(controller)
                        game.run(screen)
                    elif selected_option == 1:  # Multiplayer
                        # Start multiplayer game
                        multiplayer_mode()
                    elif selected_option == 2:  # Quit
                        pygame.quit()
                        sys.exit()

            # Controller controls
            if controller:
                # D-pad navigation
                if event.type == pygame.JOYHATMOTION:
                    hat_x, hat_y = controller.get_hat(0)
                    if hat_y == 1 and button_cooldown <= 0:  # Up
                        selected_option = (selected_option - 1) % len(menu_options)
                        button_cooldown = cooldown_time
                    elif hat_y == -1 and button_cooldown <= 0:  # Down
                        selected_option = (selected_option + 1) % len(menu_options)
                        button_cooldown = cooldown_time

                # Analog stick navigation
                if event.type == pygame.JOYAXISMOTION:
                    left_stick_y = controller.get_axis(1)
                    deadzone = 0.5

                    if left_stick_y < -deadzone and button_cooldown <= 0:
                        selected_option = (selected_option - 1) % len(menu_options)
                        button_cooldown = cooldown_time
                    elif left_stick_y > deadzone and button_cooldown <= 0:
                        selected_option = (selected_option + 1) % len(menu_options)
                        button_cooldown = cooldown_time

                # Button selection
                if event.type == pygame.JOYBUTTONDOWN:
                    # X button (0) to select
                    if controller.get_button(0):
                        if selected_option == 0:  # Single Player
                            # Start single player game
                            game = SinglePlayerGame(controller)
                            game.run(screen)
                        elif selected_option == 1:  # Multiplayer
                            # Start multiplayer game
                            multiplayer_mode()
                        elif selected_option == 2:  # Quit
                            pygame.quit()
                            sys.exit()

        # Update the display
        pygame.display.flip()


def main():
    """Main entry point"""
    main_menu()


if __name__ == "__main__":
    main()