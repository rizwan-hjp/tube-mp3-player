import flet as ft
import yt_dlp
import os
import pygame
import threading
import re
import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('music_library.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_database()
        
    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL,
                thumbnail_url TEXT,
                duration INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        
    def add_song(self, title, file_path, thumbnail_url, duration):
        self.cursor.execute('''
            INSERT INTO songs (title, file_path, thumbnail_url, duration)
            VALUES (?, ?, ?, ?)
        ''', (title, file_path, thumbnail_url, duration))
        self.conn.commit()
        
    def get_all_songs(self):
        self.cursor.execute('SELECT * FROM songs ORDER BY added_date DESC')
        return self.cursor.fetchall()
        
    def delete_song(self, song_id):
        self.cursor.execute('SELECT file_path FROM songs WHERE id = ?', (song_id,))
        file_path = self.cursor.fetchone()[0]
        if os.path.exists(file_path):
            os.remove(file_path)
        self.cursor.execute('DELETE FROM songs WHERE id = ?', (song_id,))
        self.conn.commit()
        return file_path

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playing = False
        self.current_file = None
        self.paused = False
        self.volume = 1.0  # Range 0.0 to 1.0

    def play(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False

            if self.playing and not self.paused:
                self.stop()

            if not self.paused:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                pygame.mixer.music.set_volume(self.volume)
            else:
                pygame.mixer.music.unpause()
                self.paused = False

            self.playing = True
            self.current_file = file_path
            return True
        except Exception as e:
            print(f"Error playing audio: {str(e)}")
            return False

    def stop(self):
        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False
            self.paused = False

    def pause(self):
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
            self.paused = True

    def resume(self):
        if self.paused and self.current_file:
            self.play(self.current_file)

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)

    def get_volume(self):
        return self.volume

class YouTubeDownloader:
    def __init__(self):
        # Get the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.downloads_dir = os.path.join(script_dir, 'downloads')
        
        # Create downloads directory if it doesn't exist
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir)
        
        print(f"Downloads directory: {self.downloads_dir}")
        
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
        # Remove emojis and special characters
        title = re.sub(r'[^\x00-\x7F]+', '', title)
        # Replace spaces and other characters with underscores
        title = re.sub(r'[^\w\s-]', '_', title)
        title = re.sub(r'[-\s]+', '_', title)
        # Trim to reasonable length and strip
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

    def download(self, url, progress_callback=None):
        class ProgressHook:
            def __call__(self, d):
                if d['status'] == 'downloading' and progress_callback:
                    try:
                        progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        progress_callback(progress)
                    except:
                        pass
                elif d['status'] == 'finished':
                    print(f"Download finished: {d['filename']}")

        try:
            # Get video info first
            info = self.get_video_info(url)
            sanitized_title = info['title']
            
            # Set the exact output template
            self.ydl_opts['outtmpl'] = os.path.join(self.downloads_dir, f"{sanitized_title}.%(ext)s")
            self.ydl_opts['progress_hooks'] = [ProgressHook()]

            # Perform the download
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])

            # Construct the expected file path
            expected_file = os.path.join(self.downloads_dir, f"{sanitized_title}.mp3")
            print(f"Expected file path: {expected_file}")

            # Wait briefly for file system to catch up
            import time
            time.sleep(1)

            # Verify file exists
            if os.path.exists(expected_file):
                print(f"File found at: {expected_file}")
                return expected_file
            else:
                print("Files in downloads directory:")
                for file in os.listdir(self.downloads_dir):
                    print(f"- {file}")
                raise Exception("Downloaded file not found")

        except Exception as e:
            print(f"Download error: {str(e)}")
            raise Exception(f"Error downloading: {str(e)}")

def format_duration(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

def main(page: ft.Page):
    # Initialize components
    db = Database()
    audio_player = AudioPlayer()
    youtube_downloader = YouTubeDownloader()
    
    # Setup page
    page.title = "Professional YouTube MP3 Player"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 800
    page.window_height = 600

    # UI Components
    url_input = ft.TextField(
        label="YouTube URL",
        hint_text="Paste YouTube URL here...",
        width=500,
        bgcolor=ft.colors.SURFACE_VARIANT
    )

    progress_bar = ft.ProgressBar(width=500, visible=False)
    status_text = ft.Text()
    video_title = ft.Text(size=20, weight=ft.FontWeight.BOLD)

    # Playback controls
    play_button = ft.IconButton(
        icon=ft.icons.PLAY_ARROW,
        disabled=True,
        icon_color=ft.colors.GREEN,
        icon_size=32
    )

    stop_button = ft.IconButton(
        icon=ft.icons.STOP,
        disabled=True,
        icon_color=ft.colors.RED,
        icon_size=32
    )

    prev_button = ft.IconButton(
        icon=ft.icons.SKIP_PREVIOUS,
        disabled=True,
        icon_color=ft.colors.BLUE,
        icon_size=32
    )

    next_button = ft.IconButton(
        icon=ft.icons.SKIP_NEXT,
        disabled=True,
        icon_color=ft.colors.BLUE,
        icon_size=32
    )

    # Volume control
    volume_slider = ft.Slider(
        min=0,
        max=100,
        value=40,
        label="Volume",
        width=200,
    )

    def on_volume_change(e):
        volume = e.control.value / 100
        audio_player.set_volume(volume)

    volume_slider.on_change = on_volume_change

    # Playlist table
    playlist_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Title")),
            ft.DataColumn(ft.Text("Duration")),
            ft.DataColumn(ft.Text("Actions")),
        ],
        rows=[],
    )

    def refresh_playlist():
        songs = db.get_all_songs()
        playlist_table.rows.clear()
        
        for song in songs:
            song_id, title, file_path, thumbnail, duration, _ = song
            
            play_song_button = ft.IconButton(
                icon=ft.icons.PLAY_CIRCLE,
                icon_color=ft.colors.GREEN,
                data=file_path,
                tooltip="Play"
            )
            
            delete_button = ft.IconButton(
                icon=ft.icons.DELETE,
                icon_color=ft.colors.RED,
                data=song_id,
                tooltip="Delete"
            )

            def play_from_playlist(e):
                file_path = e.control.data
                if audio_player.play(file_path):
                    play_button.icon = ft.icons.PAUSE
                    play_button.disabled = False
                    stop_button.disabled = False
                    status_text.value = "Playing..."
                page.update()

            def delete_from_playlist(e):
                song_id = e.control.data
                db.delete_song(song_id)
                refresh_playlist()
                page.update()

            play_song_button.on_click = play_from_playlist
            delete_button.on_click = delete_from_playlist

            playlist_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(title)),
                        ft.DataCell(ft.Text(format_duration(duration))),
                        ft.DataCell(
                            ft.Row([play_song_button, delete_button])
                        ),
                    ]
                )
            )
    # Initial playlist load
    refresh_playlist()
    
    def update_progress(progress):
        progress_bar.value = progress / 100
        page.update()

    def download_thread(url):
        try:
            progress_bar.visible = True
            status_text.value = "Getting video info..."
            page.update()

            info = youtube_downloader.get_video_info(url)
            video_title.value = info['original_title']
            page.update()

            status_text.value = "Downloading and converting..."
            page.update()

            file_path = youtube_downloader.download(url, update_progress)
            
            if os.path.exists(file_path):
                # Save to database
                db.add_song(
                    info['original_title'],
                    file_path,
                    info['thumbnail'],
                    info['duration']
                )
                
                refresh_playlist()
                status_text.value = "Ready to play!"
                play_button.disabled = False
                stop_button.disabled = False
            else:
                raise Exception(f"File not found: {file_path}")

        except Exception as e:
            status_text.value = f"Error: {str(e)}"
            play_button.disabled = True
            stop_button.disabled = True
        finally:
            progress_bar.visible = False
            url_input.disabled = False
            page.update()

    def start_download(e):
        if not url_input.value:
            status_text.value = "Please enter a YouTube URL"
            page.update()
            return

        url_input.disabled = True
        threading.Thread(target=download_thread, args=(url_input.value,), daemon=True).start()

    def play_audio(e):
        if audio_player.current_file and os.path.exists(audio_player.current_file):
            if not audio_player.playing:
                if audio_player.paused:
                    audio_player.resume()
                else:
                    success = audio_player.play(audio_player.current_file)
                    if not success:
                        status_text.value = "Error playing audio"
                        page.update()
                        return
                play_button.icon = ft.icons.PAUSE
            else:
                audio_player.pause()
                play_button.icon = ft.icons.PLAY_ARROW
            page.update()

    def stop_audio(e):
        audio_player.stop()
        play_button.icon = ft.icons.PLAY_ARROW
        page.update()

    play_button.on_click = play_audio
    stop_button.on_click = stop_audio

    download_button = ft.ElevatedButton(
        "Download",
        on_click=start_download,
        style=ft.ButtonStyle(
            color={ft.MaterialState.DEFAULT: ft.colors.WHITE},
            bgcolor={ft.MaterialState.DEFAULT: ft.colors.BLUE},
        )
    )

    # Layout
    page.add(
        ft.Column(
            [
                ft.Text("Professional YouTube MP3 Player", size=30, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.Row(
                    [url_input, download_button],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=20),
                progress_bar,
                status_text,
                ft.Container(height=10),
                video_title,
                ft.Container(height=20),
                ft.Row(
                    [
                        prev_button,
                        play_button,
                        stop_button,
                        next_button,
                        ft.Container(width=20),
                        ft.Icon(name=ft.icons.VOLUME_UP),
                        volume_slider,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=20),
                ft.Text("Your Music Library", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=playlist_table,
                    padding=10,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    border_radius=10,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )



    def page_cleanup():
        audio_player.stop()
        db.conn.close()

    page.on_close = page_cleanup

if __name__ == '__main__':
    ft.app(target=main)