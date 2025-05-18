# setup_sound.py
import os
import pygame

class SoundManager:
    """Simple sound manager for Tetris game."""
    
    def __init__(self):
        """Initialize the sound manager."""
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.sounds = {}
        self.music_loaded = False
        
        # Folder paths to search for audio files
        self.sound_paths = [
            "sounds/",
            "assets/sounds/",
            "./sounds/",
            "../sounds/",
            ""  # Current directory
        ]
        
        self.music_paths = [
            "sounds/",
            "assets/music/",
            "music/",
            "./sounds/",
            "../sounds/",
            ""  # Current directory
        ]
        
    def find_file(self, filename, paths):
        """Find a file by trying different paths."""
        for path in paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                print(f"Found audio file: {full_path}")
                return full_path
        return None
    
    def load_sound(self, name, filename):
        """Load a sound effect and store it with the given name."""
        file_path = self.find_file(filename, self.sound_paths)
        if file_path:
            try:
                self.sounds[name] = pygame.mixer.Sound(file_path)
                print(f"Loaded sound: {name}")
                return True
            except pygame.error as e:
                print(f"Failed to load sound '{filename}': {e}")
        else:
            print(f"Could not find sound file: {filename}")
        
        # Create a dummy sound if loading fails
        class DummySound:
            def play(self): pass
            def stop(self): pass
        self.sounds[name] = DummySound()
        return False
        
    def load_music(self, filename):
        """Load background music."""
        file_path = self.find_file(filename, self.music_paths)
        if file_path:
            try:
                pygame.mixer.music.load(file_path)
                self.music_loaded = True
                print(f"Loaded music: {filename}")
                return True
            except pygame.error as e:
                print(f"Failed to load music '{filename}': {e}")
        else:
            print(f"Could not find music file: {filename}")
        
        self.music_loaded = False
        return False
    
    def play_sound(self, name):
        """Play a loaded sound effect."""
        if name in self.sounds:
            self.sounds[name].play()
            
    def play_music(self, loops=-1, volume=0.5):
        """Play the loaded background music."""
        if self.music_loaded:
            try:
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops)
                return True
            except pygame.error as e:
                print(f"Failed to play music: {e}")
        return False
    
    def stop_music(self):
        """Stop the currently playing music."""
        try:
            pygame.mixer.music.stop()
        except pygame.error as e:
            print(f"Failed to stop music: {e}")

# Create a global instance
sound_manager = SoundManager()

def load_game_sounds():
    """Load all game sounds."""
    # Load sound effects
    sound_manager.load_sound("rotate", "rotate.wav")
    sound_manager.load_sound("clear", "clear.wav")
    sound_manager.load_sound("drop", "drop.wav")
    sound_manager.load_sound("game_over", "game_over.wav")
    
    # Load music
    sound_manager.load_music("game_music.mp3")
    
def play_sound(name):
    """Play a sound effect by name."""
    sound_manager.play_sound(name)
    
def play_music(volume=0.5):
    """Start playing the background music."""
    sound_manager.play_music(volume=volume)
    
def stop_music():
    """Stop the background music."""
    sound_manager.stop_music()