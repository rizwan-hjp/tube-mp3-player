import yt_dlp
import os
import re
import subprocess
import sys
import flet as ft
from pathlib import Path

class YouTubeDownloader:
    def __init__(self, bottom_sheet):
        # Set downloads directory to C:/_music_
        self.downloads_dir = "C:/_music_"
        
        # Add cancel flag
        self.cancel_flag = False
        self.current_download = None
        
        # Reference to BottomSheet for error display
        self.bottom_sheet = bottom_sheet
        
        # Setup FFmpeg path
        self.setup_ffmpeg()
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.downloads_dir):
            try:
                os.makedirs(self.downloads_dir)
            except PermissionError:
                self.show_error("No permission to create directory C:/_music_. Try running as administrator.")
                raise Exception("Permission Error")
            except Exception as e:
                self.show_error(f"Error creating directory: {str(e)}")
                raise Exception(f"Error creating directory: {str(e)}")
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.downloads_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True
        }

    def setup_ffmpeg(self):
        """Setup FFmpeg path for both development and packaged environments."""
        if getattr(sys, 'frozen', False):
            # If the application is running in a bundle
            base_path = sys._MEIPASS
        else:
            # If running in a normal Python environment
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Look for FFmpeg in common locations
        possible_paths = [
            os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe'),  # In ffmpeg subdirectory
            os.path.join(base_path, 'ffmpeg.exe'),            # Direct in application directory
            'ffmpeg.exe',                                     # In system PATH
        ]
        
        self.ffmpeg_path = None
        for path in possible_paths:
            if os.path.exists(path) or self.check_ffmpeg_in_path(path):
                self.ffmpeg_path = path
                break
                
        if not self.ffmpeg_path:
            self.show_error("FFmpeg not found. Please ensure FFmpeg is installed and in the application directory.")
            raise Exception("FFmpeg not found")

    def check_ffmpeg_in_path(self, command):
        """Check if FFmpeg is available in system PATH."""
        try:
            subprocess.run([command, "-version"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def sanitize_filename(self, title):
        """Sanitize the filename to remove invalid characters."""
        title = re.sub(r'[^\x00-\x7F]+', '', title)
        title = re.sub(r'[^\w\s-]', '_', title)
        title = re.sub(r'[-\s]+', '_', title)
        title = title[:100].strip('_')
        return title

    def show_error(self, message):
        """Show the error in the Flet BottomSheet."""
        self.bottom_sheet.content = ft.Text(message)
        self.bottom_sheet.open = True

    def cancel_download(self):
        """Cancel the current download if one is in progress."""
        try:
            # Set the cancel flag to trigger the progress hook to stop
            self.cancel_flag = True
            
            # If there's an active download, stop it
            if self.current_download:
                try:
                    # Attempt to abort the current download
                    self.current_download.break_download()
                except:
                    pass  # Ignore any errors from breaking the download
                
            return True
        except Exception as e:
            self.show_error(f"Error cancelling download: {str(e)}")
            return False

    def get_video_info(self, url):
        """Get video information before downloading."""
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                sanitized_title = self.sanitize_filename(info['title'])
                return {
                    'title': sanitized_title,
                    'duration': info['duration'],
                    'thumbnail': info['thumbnail'],
                    'original_title': info['title']
                }
            except Exception as e:
                self.show_error(f"Error getting video info: {str(e)}")
                raise Exception(f"Error getting video info: {str(e)}")

    def convert_to_mp3(self, input_file):
        """Convert downloaded file to MP3 format."""
        try:
            output_file = os.path.splitext(input_file)[0] + '.mp3'
            
            # Build FFmpeg command
            command = [
                self.ffmpeg_path,
                '-i', input_file,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',  # Overwrite output file
                '-hide_banner',  # Hide FFmpeg compilation info
                '-loglevel', 'error',  # Only show errors
                output_file
            ]
            
            # Run FFmpeg process with hidden window
            startupinfo = None
            if os.name == 'nt':  # If on Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Run the process
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Check if output file was created
            if not os.path.exists(output_file):
                raise Exception("FFmpeg failed to create output file")
                
            print(f"Conversion to MP3 successful: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            self.show_error(f"Error converting to MP3: {error_message}")
            raise Exception(f"Error converting to MP3: {error_message}")
        except Exception as e:
            self.show_error(f"Error converting to MP3: {str(e)}")
            raise Exception(f"Error converting to MP3: {str(e)}")
    
    def download(self, url, progress_callback=None):
        """Download and convert a YouTube video to MP3."""
        # Reset cancel flag at start of new download
        self.cancel_flag = False
        
        class ProgressHook:
            def __init__(self, outer):
                self.outer = outer
                
            def __call__(self, d):
                # Check if download should be cancelled
                if self.outer.cancel_flag:
                    raise Exception("Download cancelled by user")
                    
                if d['status'] == 'downloading' and progress_callback:
                    try:
                        progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        progress_callback(progress)
                    except:
                        pass
                elif d['status'] == 'finished':
                    print(f"Download finished: {d['filename']}")

        try:
            info = self.get_video_info(url)
            sanitized_title = info['title']
            
            # Check if file already exists
            output_file = os.path.join(self.downloads_dir, f"{sanitized_title}.webm")
            counter = 1
            while os.path.exists(output_file):
                new_title = f"{sanitized_title}_{counter}"
                output_file = os.path.join(self.downloads_dir, f"{new_title}.webm")
                counter += 1
            
            # Update output template with new filename
            self.ydl_opts['outtmpl'] = os.path.join(
                self.downloads_dir, 
                f"{os.path.splitext(os.path.basename(output_file))[0]}.%(ext)s"
            )
            self.ydl_opts['progress_hooks'] = [ProgressHook(self)]
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                self.current_download = ydl
                ydl.download([url])
            
            # Clear current download after completion
            self.current_download = None

            # Convert the downloaded file to MP3
            mp3_file = self.convert_to_mp3(output_file)
            
            # Clean up the original file after conversion
            try:
                os.remove(output_file)
            except:
                pass
                
            return mp3_file
            
        except Exception as e:
            if str(e) == "Download cancelled by user":
                # Clean up partially downloaded files
                try:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                except:
                    pass
                self.show_error("Download cancelled by user")
                raise Exception("Download cancelled")
            elif isinstance(e, PermissionError):
                self.show_error("No permission to write to C:/_music_. Try running as administrator.")
                raise Exception("No permission to write to C:/_music_. Try running as administrator.")
            else:
                self.show_error(f"Error downloading: {str(e)}")
                raise Exception(f"Error downloading: {str(e)}")
        finally:
            self.current_download = None