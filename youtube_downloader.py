import yt_dlp
import os
import re
import subprocess
import sys
import requests

class YouTubeDownloader:
    def __init__(self):
        # Set downloads directory to _music_ folder in the app directory
        current_dir = os.getcwd()
        self.downloads_dir = os.path.join(current_dir, "_music_")

        # Ensure the _music_ folder exists, create if not
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        # Add cancel flag
        self.cancel_flag = False
        
        # Setup FFmpeg path
        self.setup_ffmpeg()
        
        # Configure YDL options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.downloads_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True
        }

    def setup_ffmpeg(self):
        """Setup FFmpeg path for both development and packaged environments."""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        ffmpeg_folder = os.path.join(base_path, 'assets', 'ffmpeg')
        self.ffmpeg_path = os.path.join(ffmpeg_folder, 'ffmpeg.exe')

        if not os.path.exists(self.ffmpeg_path):
            raise FileNotFoundError(f"FFmpeg not found in {ffmpeg_folder}. Please ensure it is properly placed.")

    def log_error(self, message):
        """Log an error message."""
        print(f"ERROR: {message}")

    def sanitize_filename(self, title):
        """Sanitize the filename to remove invalid characters."""
        title = re.sub(r'[^\x00-\x7F]+', '', title)
        title = re.sub(r'[^\w\s-]', '_', title)
        title = re.sub(r'[-\s]+', '_', title)
        return title[:100].strip('_')

    def get_video_info(self, url):
        """Retrieve information about the video."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                sanitized_title = self.sanitize_filename(info['title'])
                return {
                    'title': sanitized_title,
                    'duration': info['duration'],
                    'thumbnail': info['thumbnail'],
                    'original_title': info['title']
                }
        except Exception as e:
            self.log_error(f"Error getting video info: {str(e)}")
            raise

    def cancel_download(self):
        """Cancel the current download."""
        self.cancel_flag = True

    def convert_to_mp3(self, input_file):
        """Convert the downloaded file to MP3."""
        try:
            output_file = os.path.splitext(input_file)[0] + '.mp3'
            command = [
                self.ffmpeg_path,
                '-i', input_file,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',
                '-hide_banner',
                '-loglevel', 'error',
                output_file
            ]

            startupinfo = None
            if os.name == 'nt':  # On Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if not os.path.exists(output_file):
                raise Exception("FFmpeg failed to create output file")
            
            print(f"Conversion to MP3 successful: {output_file}")
            return output_file
        except Exception as e:
            self.log_error(f"Error converting to MP3: {str(e)}")
            raise

    def download_thumbnail(self, thumbnail_url, title):
        """Download the thumbnail and save it as an MP3 file."""
        try:
            response = requests.get(thumbnail_url, stream=True)
            if response.status_code == 200:
                sanitized_title = self.sanitize_filename(title)
                thumbnail_path = os.path.join(self.downloads_dir, f"{sanitized_title}_thumbnail.jpg")
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                print(f"Thumbnail saved as MP3: {thumbnail_path}")
                return thumbnail_path
            else:
                self.log_error("Failed to download thumbnail.")
        except Exception as e:
            self.log_error(f"Error downloading thumbnail: {str(e)}")
            raise

    def download(self, url, progress_callback=None):
        """Download a YouTube video and convert it to MP3."""
        self.cancel_flag = False

        def progress_hook(d):
            if self.cancel_flag:
                raise Exception("Download cancelled by user")
            if d['status'] == 'downloading' and progress_callback:
                progress = (d.get('downloaded_bytes', 0) / d.get('total_bytes', 1)) * 100
                progress_callback(progress)

        try:
            info = self.get_video_info(url)
            sanitized_title = info['title']

            output_file = os.path.join(self.downloads_dir, f"{sanitized_title}.webm")
            counter = 1
            while os.path.exists(output_file):
                output_file = os.path.join(self.downloads_dir, f"{sanitized_title}_{counter}.webm")
                counter += 1
            
            self.ydl_opts['outtmpl'] = output_file
            self.ydl_opts['progress_hooks'] = [progress_hook]

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
            
            mp3_file = self.convert_to_mp3(output_file)

            # Download the thumbnail 
            thumbnail = self.download_thumbnail(info['thumbnail'], sanitized_title)
       
            return mp3_file, thumbnail  # Return as a tuple
        except Exception as e:
            if "Download cancelled by user" in str(e):
                self.log_error("Download cancelled by user")
            else:
                self.log_error(f"Error downloading: {str(e)}")
            raise