import time
import threading
import os
import sys
import ctypes

# Global vlc import after DLL loading
vlc = None

class AudioPlayer:
    def __init__(self):
        # Get the directory where the script is located
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            base_path = sys._MEIPASS
        else:
            # If running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # VLC folder will be in the same directory as the script
        vlc_path = os.path.join(base_path, 'vlc')
        
        # Ensure the path exists
        if not os.path.exists(vlc_path):
            raise Exception(f"VLC directory not found at: {vlc_path}")

        if sys.platform.startswith('win'):
            # Manually load the VLC DLLs in the correct order
            os.add_dll_directory(vlc_path)
            
            # First load libvlccore, then libvlc
            libvlccore_path = os.path.join(vlc_path, 'libvlccore.dll')
            libvlc_path = os.path.join(vlc_path, 'libvlc.dll')
            
            if not os.path.exists(libvlccore_path) or not os.path.exists(libvlc_path):
                raise Exception("Required VLC DLLs not found")
            
            # Load the DLLs
            ctypes.CDLL(libvlccore_path)
            ctypes.CDLL(libvlc_path)

            # Add to PATH and set plugin path
            os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']
            plugin_path = os.path.join(vlc_path, 'plugins')
        else:
            plugin_path = os.path.join(vlc_path, 'vlc', 'plugins')

        # Import vlc module globally after DLLs are loaded
        global vlc
        import vlc
        
        # Create VLC instance with plugin path
        self.instance = vlc.Instance(
            '--no-xlib',
            f'--plugin-path={plugin_path}',
        )
        
        self.player = self.instance.media_player_new()
        self.current_file = None
        self.playing = False
        self.paused = False
        self.on_complete_callback = None
        self.on_position_update_callback = None
        self.on_duration_callback = None
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        
        # Store VLC states
        self.State = vlc.State

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
            self.stop_monitoring.set()
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.stop_monitoring.clear()

            self.current_file = file_path
            self.current_media = self.instance.media_new(file_path)
            self.player.set_media(self.current_media)
            self.player.play()
            self.playing = True
            self.player.audio_set_volume(int(0.5 * 100))

            # Wait for the player to load and retrieve duration
            time.sleep(0.1)
            duration = self.player.get_length() / 1000.0
            if self.on_duration_callback:
                self.on_duration_callback(duration)

            # Restart monitoring for the new song
            self.stop_monitoring.clear()
            self._start_monitoring()
            return True
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False

    def _start_monitoring(self):
        """Monitor playback state and invoke callbacks."""
        def monitor_playback():
            while not self.stop_monitoring.is_set():
                if self.player.get_state() == self.State.Ended:  # Using stored State
                    self.playing = False
                    if self.on_complete_callback:
                        self.on_complete_callback()
                    break

                if self.playing:
                    position = self.player.get_time() / 1000.0
                    if self.on_position_update_callback:
                        self.on_position_update_callback(position)
                time.sleep(0.1)

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
            self.stop_monitoring.clear()
            self._start_monitoring()

    def stop(self):
        """Stop playback."""
        self.stop_monitoring.set()
        self.player.stop()
        self.playing = False
        self.paused = False
        self.current_file = None

    def seek(self, position):
        """Seek to a position in seconds."""
        if self.current_file:
            self.player.set_time(int(position * 1000))

    def set_volume(self, volume):
        """Set the playback volume (0 to 1.0)."""
        volume = max(0.0, min(volume, 1.0))
        self.player.audio_set_volume(int(volume * 100))