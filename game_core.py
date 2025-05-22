# game_core.py - Bridge module to connect existing game files with main menu

from single_player import SinglePlayerGame
from multiplayer import multiplayer_mode

class MultiplayerGame:
    """Wrapper class for multiplayer mode to match main.py expectations"""
    def __init__(self, controller=None):
        self.controller = controller
    
    def run(self, screen):
        """Run multiplayer game and return to main menu"""
        multiplayer_mode()

# Make SinglePlayerGame available (it's already properly structured)
# The SinglePlayerGame class from single_player.py is already compatible
