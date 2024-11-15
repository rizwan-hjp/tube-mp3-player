import yt_dlp
import os
import re
import threading

class YouTubeDownloader:
    def __init__(self):
        # Set downloads directory to C:/_music_
        self.downloads_dir = "C:/_music_"
        
        # Add cancel flag
        self.cancel_flag = False
        self.current_download = None
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.downloads_dir):
            try:
                os.makedirs(self.downloads_dir)
            except PermissionError:
                raise Exception("No permission to create directory C:/_music_. Try running as administrator.")
            except Exception as e:
                raise Exception(f"Error creating directory: {str(e)}")
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.downloads_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True
        }

    def sanitize_filename(self, title):
        title = re.sub(r'[^\x00-\x7F]+', '', title)
        title = re.sub(r'[^\w\s-]', '_', title)
        title = re.sub(r'[-\s]+', '_', title)
        title = title[:100].strip('_')
        return title

    def get_video_info(self, url):
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
                raise Exception(f"Error getting video info: {str(e)}")

    def cancel_download(self):
        """Cancel the current download if one is in progress."""
        self.cancel_flag = True
        if self.current_download:
            self.current_download.cancel()

    def download(self, url, progress_callback=None):
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
            output_file = os.path.join(self.downloads_dir, f"{sanitized_title}.mp3")
            counter = 1
            while os.path.exists(output_file):
                new_title = f"{sanitized_title}_{counter}"
                output_file = os.path.join(self.downloads_dir, f"{new_title}.mp3")
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
            
            if os.path.exists(output_file):
                return output_file
            else:
                raise Exception("Downloaded file not found")
                
        except Exception as e:
            if str(e) == "Download cancelled by user":
                # Clean up partially downloaded files
                try:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                except:
                    pass
                raise Exception("Download cancelled")
            elif isinstance(e, PermissionError):
                raise Exception("No permission to write to C:/_music_. Try running as administrator.")
            else:
                raise Exception(f"Error downloading: {str(e)}")
        finally:
            self.current_download = None