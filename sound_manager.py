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
        pygame.mixer.init()
    
    # Define sound file paths (assuming files are in a 'sounds' directory)
    sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
    
    # Create sounds directory if it doesn't exist
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
        print(f"Created sounds directory at {sounds_dir}")
        print("You'll need to add sound files to this directory.")
    
    # Dictionary mapping sound names to file paths
    sound_files = {
        "rotate": os.path.join(sounds_dir, "rotate.wav"),
        "drop": os.path.join(sounds_dir, "drop.wav"),
        "clear": os.path.join(sounds_dir, "clear.wav"),
        "game_over": os.path.join(sounds_dir, "game_over.wav"),
        "menu_select": os.path.join(sounds_dir, "menu_select.wav")
    }
    
    # Load each sound file if it exists, otherwise create placeholder
    for name, filepath in sound_files.items():
        if os.path.exists(filepath):
            sound_effects[name] = pygame.mixer.Sound(filepath)
            # Set default volume
            if name in default_volumes:
                sound_effects[name].set_volume(default_volumes[name])
        else:
            # Create a placeholder silent sound
            sound_effects[name] = pygame.mixer.Sound(buffer=bytearray())
            print(f"Sound file not found: {filepath}")

def play_sound(sound_name):
    """Play a sound effect by name"""
    if sound_name in sound_effects:
        sound_effects[sound_name].play()
    else:
        print(f"Sound '{sound_name}' not found")

def play_music(music_file="game_music.mp3", volume=0.5, loop=-1):
    """Start playing background music"""
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        
    music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
    music_path = os.path.join(music_dir, music_file)
    
    try:
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loop)
        else:
            print(f"Music file not found: {music_path}")
    except pygame.error as e:
        print(f"Error playing music: {e}")

def stop_music():
    """Stop currently playing music"""
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

def ensure_music_playing(volume=0.5):
    """Make sure music is playing; restart if stopped"""
    if pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
        play_music(volume=volume)