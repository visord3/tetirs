import pygame
import os

# Dictionary to store loaded sound effects
sound_effects = {}
default_volumes = {
    "rotate": 0.3,
    "drop": 0.4,
    "clear": 0.5,
    "game_over": 0.7
}

def load_game_sounds():
    """Load all game sound effects"""
    global sound_effects
    
    # Initialize pygame mixer if not already initialized
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except pygame.error:
            print("Could not initialize pygame mixer")
    
    # Create dummy sounds if mixer is not available
    class DummySound:
        def play(self): pass
        def stop(self): pass
        def set_volume(self, vol): pass
    
    # Create all sounds as dummy sounds for now
    sound_effects = {
        "rotate": DummySound(),
        "drop": DummySound(),
        "clear": DummySound(),
        "game_over": DummySound(),
        "menu_select": DummySound()
    }
    
    print("Loaded dummy sound effects")

def play_sound(sound_name):
    """Play a sound effect by name"""
    if sound_name in sound_effects:
        sound_effects[sound_name].play()
    else:
        print(f"Sound '{sound_name}' not found")

def play_music(music_file="game_music.mp3", volume=0.5, loop=-1):
    """Start playing background music"""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except pygame.error:
        print("Could not initialize mixer for music")
        return
    
    # For now, just print that music would be playing
    print(f"Music would be playing: {music_file} at volume {volume}")

def stop_music():
    """Stop currently playing music"""
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

def ensure_music_playing(volume=0.5):
    """Make sure music is playing; restart if stopped"""
    # For now, just pass since we don't have actual music files
    pass