import pygame
import os

# Sound file paths
SOUND_DIR = "sounds"
SOUND_FILES = {
    "menu_select": "menu_select.wav",
    "menu_move": "menu_move.wav",
    "rotate": "rotate.wav",
    "drop": "drop.wav",
    "clear": "clear.wav",
    "game_over": "game_over.wav",
    "level_up": "level_up.wav",
    "move": "move.wav"
}
MUSIC_FILE = "tetris music.mp3"  # Note: Using the exact filename with space

# Sound manager instance
_sound_manager = None

def get_sound_manager():
    """Get or create the sound manager instance"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_loaded = False
        self.sound_enabled = True
        self.music_volume = 0.7
        self.effects_volume = 0.5
        self._init_sounds()
    
    def _init_sounds(self):
        """Initialize game sounds"""
        try:
            # Create sound effects
            for name, filename in SOUND_FILES.items():
                filepath = os.path.join(SOUND_DIR, filename)
                if os.path.exists(filepath):
                    self.sounds[name] = pygame.mixer.Sound(filepath)
                    self.sounds[name].set_volume(self.effects_volume)
                else:
                    # print(f"Warning: Sound file not found: {filepath}")
                    pass
            # Load music
            music_path = os.path.join(SOUND_DIR, MUSIC_FILE)
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                self.music_loaded = True
            else:
                # print(f"Warning: Music file not found: {music_path}")
                pass
        except Exception as e:
            # print(f"Error loading sounds: {e}")
            self._init_dummy_sounds()
    
    def _init_dummy_sounds(self):
        """Initialize dummy sounds as fallback"""
        class DummySound:
            def play(self): pass
            def stop(self): pass
            def set_volume(self, vol): pass
        
        self.sounds = {
            "menu_select": DummySound(),
            "menu_move": DummySound(),
            "rotate": DummySound(),
            "drop": DummySound(),
            "clear": DummySound(),
            "game_over": DummySound(),
            "level_up": DummySound(),
            "move": DummySound()
        }
    
    def play_sound(self, name):
        """Play a sound effect"""
        if self.sound_enabled and name in self.sounds:
            self.sounds[name].play()
    
    def play_music(self):
        """Play background music"""
        if self.sound_enabled and self.music_loaded:
            try:
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except:
                pass
    
    def stop_music(self):
        """Stop background music"""
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except:
            pass
    
    def set_sound_enabled(self, enabled):
        """Enable or disable all sounds"""
        self.sound_enabled = enabled
        if not enabled:
            self.stop_music()
        elif enabled and self.music_loaded:
            self.play_music()

# Global functions for easy access
def load_game_sounds():
    """Load all game sounds"""
    get_sound_manager()

def play_sound(name):
    """Play a sound effect"""
    get_sound_manager().play_sound(name)

def play_music():
    """Play background music"""
    get_sound_manager().play_music()

def stop_music():
    """Stop background music"""
    get_sound_manager().stop_music()

def ensure_music_playing():
    """Ensure music is playing if it should be"""
    manager = get_sound_manager()
    if manager.sound_enabled and manager.music_loaded and not pygame.mixer.music.get_busy():
        manager.play_music()