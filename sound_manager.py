# setup_sound.py - complete rewrite with more robust sound handling
import os
import pygame
import time

class SoundManager:
    """
    Robust sound manager for Tetris game.
    Handles music looping and sound effects with detailed error handling.
    """
    
    def __init__(self):
        """Initialize the sound manager with robust error handling."""
        # Make sure pygame is initialized before we try to use the mixer
        if not pygame.get_init():
            pygame.init()
            
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                print("Pygame mixer initialized successfully")
            except pygame.error as e:
                print(f"Failed to initialize pygame mixer: {e}")
                # Create a fallback mixer that does nothing
                self._create_dummy_mixer()
                return
        
        self.sounds = {}
        self.music_loaded = False
        self.music_playing = False
        self.current_music_file = None
        self.music_volume = 0.7  # Default volume
        
        # Add a cooldown for music restart attempts to prevent spam
        self.last_restart_attempt = 0
        self.restart_cooldown = 2000  # 2 seconds between restart attempts
        
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
        
        # Create a dummy channel for sound effects if mixer isn't working
        try:
            # Reserve channels for sound effects to prevent cutoff
            pygame.mixer.set_reserved(1)
            self.sound_channel = pygame.mixer.Channel(0)
        except:
            print("Error setting up sound channels")
            self.sound_channel = None
    
    def _create_dummy_mixer(self):
        """Create dummy objects when mixer fails to initialize."""
        self.sounds = {}
        self.music_loaded = False
        self.music_playing = False
        
        # Create dummy mixer music
        class DummyMusicMixer:
            def load(self, filename): pass
            def play(self, loops=-1): pass
            def stop(self): pass
            def set_volume(self, volume): pass
            def get_volume(self): return 0.0
            def get_busy(self): return False
            
        pygame.mixer.music = DummyMusicMixer()
        self.sound_channel = None
        
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
        if name in self.sounds:
            # Already loaded
            return True
            
        file_path = self.find_file(filename, self.sound_paths)
        if file_path:
            try:
                self.sounds[name] = pygame.mixer.Sound(file_path)
                print(f"Loaded sound: {name} from {file_path}")
                return True
            except pygame.error as e:
                print(f"Failed to load sound '{filename}': {e}")
        else:
            print(f"Could not find sound file: {filename}")
        
        # Create a dummy sound if loading fails
        class DummySound:
            def play(self): pass
            def stop(self): pass
            def set_volume(self, volume): pass
            def get_volume(self): return 0.0
            
        self.sounds[name] = DummySound()
        return False
        
    def load_music(self, filename):
        """Load background music with robust error handling."""
        self.current_music_file = filename
        file_path = self.find_file(filename, self.music_paths)
        
        if file_path:
            try:
                pygame.mixer.music.load(file_path)
                self.music_loaded = True
                print(f"Successfully loaded music: {file_path}")
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
            try:
                if self.sound_channel:
                    self.sound_channel.play(self.sounds[name])
                else:
                    self.sounds[name].play()
            except:
                print(f"Error playing sound: {name}")
            
    def play_music(self, loops=-1, volume=None):
        """
        Play the loaded background music with error handling.
        Returns True if successful, False otherwise.
        """
        if volume is not None:
            self.music_volume = max(0.0, min(1.0, volume))
            
        if not self.music_loaded:
            print("No music loaded - cannot play")
            return False
            
        try:
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            self.music_playing = True
            self.last_restart_attempt = pygame.time.get_ticks()
            print(f"Started playing music at volume {self.music_volume}")
            return True
        except pygame.error as e:
            print(f"Failed to play music: {e}")
            self.music_playing = False
            return False
    
    def stop_music(self):
        """Stop the currently playing music with error handling."""
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
            print("Music stopped")
        except pygame.error as e:
            print(f"Failed to stop music: {e}")
    
    def ensure_music_playing(self):
        """
        Check if music should be playing and restart it if necessary.
        This helps handle cases where music stops unexpectedly.
        """
        current_time = pygame.time.get_ticks()
        
        # Only attempt restart if cooldown period has passed
        if (self.music_playing and 
            not pygame.mixer.music.get_busy() and 
            current_time - self.last_restart_attempt > self.restart_cooldown):
            
            print("Music should be playing but isn't - attempting to restart")
            # Update the restart attempt timestamp
            self.last_restart_attempt = current_time
            
            # Wait a moment before trying to restart to avoid restart loops
            time.sleep(0.1)
            try:
                self.play_music(volume=self.music_volume)
            except:
                print("Failed to restart music")
    
    def toggle_mute_music(self):
        """Toggle music between muted and unmuted."""
        if pygame.mixer.music.get_volume() > 0:
            self._previous_volume = pygame.mixer.music.get_volume()
            pygame.mixer.music.set_volume(0.0)
            print("Music muted")
            return True
        else:
            # If previously muted, restore previous volume
            try:
                if hasattr(self, '_previous_volume'):
                    volume = self._previous_volume
                else:
                    volume = self.music_volume
                pygame.mixer.music.set_volume(volume)
                print(f"Music unmuted (volume: {volume:.1f})")
                return False
            except:
                print("Error toggling mute")
                return True
                
    def adjust_volume(self, amount):
        """Adjust music volume by the given amount (-1.0 to 1.0)."""
        try:
            current = pygame.mixer.music.get_volume()
            new_volume = max(0.0, min(1.0, current + amount))
            pygame.mixer.music.set_volume(new_volume)
            self.music_volume = new_volume
            print(f"Volume adjusted to {new_volume:.1f}")
            return new_volume
        except:
            print("Error adjusting volume")
            return 0.0

# Create a global instance
sound_manager = SoundManager()

def load_game_sounds():
    """Load all game sounds."""
    # Load sound effects
    sound_manager.load_sound("rotate", "rotate.wav")
    sound_manager.load_sound("clear", "clear.wav")
    sound_manager.load_sound("drop", "drop.wav")
    sound_manager.load_sound("game_over", "game_over.wav")
    sound_manager.load_sound("level_up", "level_up.wav")
    sound_manager.load_sound("menu_move", "menu_move.wav")
    sound_manager.load_sound("menu_select", "menu_select.wav")
    sound_manager.load_sound("move", "move.wav")
    
    # Load music - update to match the correct file name in the sounds folder
    sound_manager.load_music("tetris music.mp3")
    
def play_sound(name):
    """Play a sound effect by name."""
    sound_manager.play_sound(name)
    
def play_music(volume=0.7):
    """Start playing the background music."""
    return sound_manager.play_music(volume=volume)
    
def stop_music():
    """Stop the background music."""
    sound_manager.stop_music()
    
def ensure_music_playing():
    """Make sure music is still playing."""
    sound_manager.ensure_music_playing()
    
def toggle_mute():
    """Toggle music mute state."""
    return sound_manager.toggle_mute_music()
    
def adjust_volume(amount):
    """Adjust volume by the given amount."""
    return sound_manager.adjust_volume(amount)