import vlc
import time
import threading

class AudioPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_file = None  # Track the current file
        self.playing = False
        self.paused = False
        self.on_complete_callback = None
        self.on_position_update_callback = None
        self.on_duration_callback = None
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()  # Event to stop monitoring thread

    def set_on_complete_callback(self, callback):
        self.on_complete_callback = callback

    def set_on_position_update_callback(self, callback):
        self.on_position_update_callback = callback

    def set_on_duration_callback(self, callback):
        self.on_duration_callback = callback

    def play(self, file_path):
        """Play the specified audio file."""
        try:
            # Stop any ongoing playback and monitoring
            self.stop_monitoring.set()  # Set the event to stop the previous thread
            if self.monitor_thread and self.monitor_thread.is_alive():
                # Avoid calling join() on the current thread, instead stop the monitoring thread
                self.stop_monitoring.clear()

            self.current_file = file_path
            self.current_media = self.instance.media_new(file_path)
            self.player.set_media(self.current_media)
            self.player.play()
            self.playing = True

            # Wait for the player to load and retrieve duration
            time.sleep(0.1)
            duration = self.player.get_length() / 1000.0  # Convert to seconds
            if self.on_duration_callback:
                self.on_duration_callback(duration)

            # Restart monitoring for the new song
            self.stop_monitoring.clear()  # Reset the stop event for monitoring
            self._start_monitoring()
            return True
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False

    def _start_monitoring(self):
        """Monitor playback state and invoke callbacks."""
        def monitor_playback():
            while not self.stop_monitoring.is_set():
                if self.player.get_state() == vlc.State.Ended:
                    self.playing = False
                    if self.on_complete_callback:
                        self.on_complete_callback()
                    break

                if self.playing:  # Update position only when playing
                    position = self.player.get_time() / 1000.0  # Current position in seconds
                    if self.on_position_update_callback:
                        self.on_position_update_callback(position)
                time.sleep(0.1)

        # Ensure a new thread starts if needed
        self.monitor_thread = threading.Thread(target=monitor_playback, daemon=True)
        self.monitor_thread.start()

    def pause(self):
        """Pause the currently playing audio."""
        if self.playing:
            self.player.pause()
            self.playing = False
            self.paused = True

    def resume(self):
        """Resume paused audio."""
        if self.paused:
            self.player.play()
            self.playing = True
            self.paused = False
            self.stop_monitoring.clear()  # Clear the stop event to continue monitoring
            self._start_monitoring()  # Restart monitoring if it was paused

    def stop(self):
        """Stop playback."""
        self.stop_monitoring.set()  # Stop the monitoring thread
        self.player.stop()
        self.playing = False
        self.paused = False
        self.current_file = None

    def seek(self, position):
        """Seek to a position in seconds."""
        if self.current_file:
            self.player.set_time(int(position * 1000))  # Convert to milliseconds

    def set_volume(self, volume):
        """Set the playback volume (0 to 1.0)."""
        volume = max(0.0, min(volume, 1.0))  # Clamp value between 0.0 and 1.0
        self.player.audio_set_volume(int(volume * 100))  # Set the volume (0 to 100)
