import pygame
import threading

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_file = None
        self.playing = False
        self.paused = False
        self.on_complete_callback = None
        self.on_position_update_callback = None
        self.on_duration_callback = None  # New callback for duration

    def set_on_complete_callback(self, callback):
        """Set the callback to invoke when audio playback is complete."""
        self.on_complete_callback = callback
    
    def set_on_position_update_callback(self, callback):
        """Set the callback to invoke with the current playback position."""
        self.on_position_update_callback = callback

    def set_on_duration_callback(self, callback):
        """Set the callback to invoke with the audio file's duration."""
        self.on_duration_callback = callback

    def check_if_complete(self):
        """Check if the current audio has finished playing."""
        if not pygame.mixer.music.get_busy() and self.playing and not self.paused:
            self.playing = False
            self.current_file = None
            if self.on_complete_callback:
                self.on_complete_callback()


    def play(self, file_path):
        """Play an audio file."""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.current_file = file_path
            self.playing = True
            self.paused = False
            
            sound = pygame.mixer.Sound(self.current_file)
            duration = sound.get_length()
            if self.on_duration_callback:
                self.on_duration_callback(duration)  # Invoke the callback with the duration

            # Start a thread to monitor playback completion and position updates
            def check_completion():
                while self.playing:
                    self.check_if_complete()
                    pygame.time.wait(100)
                    if self.on_position_update_callback:
                        self.on_position_update_callback(pygame.mixer.music.get_pos() / 1000)

            threading.Thread(target=check_completion, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False

    def pause(self):
        """Pause the currently playing audio."""
        if self.playing:
            pygame.mixer.music.pause()
            self.paused = True
            self.playing = False

    def resume(self):
        """Resume paused audio."""
        if self.paused:
            pygame.mixer.music.unpause()
            self.playing = True
            self.paused = False

    def stop(self):
        """Stop the currently playing audio."""
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.current_file = None

    def set_volume(self, volume):
        """Set the playback volume (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(volume)