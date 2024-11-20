import flet as ft
import os
import qr_code_server
import shutil
from urllib.parse import quote
import pathlib

class ShareMusic:
    def __init__(self, page, audio_player, queue_manager, db):
        self.page = page
        self.single_play = audio_player
        self.db = db
        self.queue_manager = queue_manager
        
        # Create necessary directories
        self.html_dir = os.path.join(os.getcwd(), "html")
        self.music_dir = os.path.join(self.html_dir, "music")
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        self.css_path = os.path.join(os.getcwd(),"assets")
        # Start the server from qr_code_server.py
        qr_code_server.start_flask_server()

        # Generate QR code with the IP and port
        self.qr_base64, self.ip_address = qr_code_server.generate_qr_code(qr_code_server.port)

        self.musicShareButton = ft.Container(
            ft.FloatingActionButton(
                icon=ft.icons.QR_CODE,
                bgcolor=ft.colors.TRANSPARENT,
                on_click=self.show_qr_code,
            ),
            alignment=ft.alignment.bottom_right,
            margin=ft.margin.all(16),
        )
       

    def show_qr_code(self, e):
        """Show QR code in a dialog."""
        all_songs = self.queue_manager.get_all_songs()

        if not all_songs:
            self.page.snack_bar = ft.SnackBar(
            content=ft.Text("No songs found in the playlist.",weight=ft.FontWeight.BOLD,color='red'),
            bgcolor='#ffd97e',
            action="Alright!",

           
             )
            self.page.snack_bar.open =True
            self.page.update()
            return

        self.serve_music_player()
      
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Scan QR Code",),
            shadow_color="red",
            content=ft.Column(
                controls=[
                    # ft.Text(f"Server running at: http://{self.ip_address}:8000", size=14),
                    ft.Image(src_base64=self.qr_base64, width=200, height=200),
                    ft.Text(f"Play Music on Mobile", size=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                height=self.page.height * 0.5,
                width=300
            ),
            actions=[ft.TextButton("Close", on_click=self.close_qr_code)],
        )
        self.page.dialog.open = True
        self.page.update()

    def close_qr_code(self, e):
        """Close the QR code dialog"""
        if self.page.dialog:
            self.page.dialog.open = False
        self.page.update()

    def prepare_music_files(self, songs):
        """Copy music files to the web-accessible directory and return their web paths."""
        print(f"Preparing music files for {len(songs)} songs")
        
        # Clear existing files
        for file in os.listdir(self.music_dir):
            file_path = os.path.join(self.music_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        web_paths = []
        for song in songs:
            try:
                # Get the song path from the song data structure
                song_path = song['song'][0] if isinstance(song, dict) else song[0]
                
                # Create a web-safe filename
                original_extension = pathlib.Path(song_path).suffix
                safe_filename = f"{hash(song_path)}{original_extension}"
                
                # Copy the file to the music directory
                dest_path = os.path.join(self.music_dir, safe_filename)
                print(f"Copying {song_path} to {dest_path}")
                shutil.copy2(song_path, dest_path)
                
                # Store the web-accessible path
                web_path = f"/music/{quote(safe_filename)}"
                web_paths.append((song, web_path))
                print(f"Added web path: {web_path}")
                
            except Exception as e:
                print(f"Error preparing file for {song}: {e}")
                continue
                
        print(f"Successfully prepared {len(web_paths)} files")
        return web_paths

    def serve_music_player(self):
        """Generate and save the music player HTML file for all songs."""
        try:
            # Fetch all songs from the queue manager
            all_songs = self.queue_manager.get_all_songs()
            print(f"Retrieved songs data: {all_songs}")
            
            if not all_songs:
                raise ValueError("No songs found in the queue")
                
            # Prepare music files and get their web paths
            songs_with_paths = self.prepare_music_files(all_songs)
            print(f"Prepared {len(songs_with_paths)} songs with web paths")

            # Build the song list for the HTML content
            song_items = []
            for song_data, web_path in songs_with_paths:
                try:
                    # Handle both dictionary and tuple formats
                    if isinstance(song_data, dict):
                        song_path = song_data['song'][0]
                        thumbnail = song_data['song'][1]
                        is_current = song_data.get('is_current', False)
                    else:
                        song_path = song_data[0]
                        thumbnail = song_data[1]
                        is_current = False

                    # Get the filename without extension as song name
                    song_name = os.path.splitext(os.path.basename(song_path))[0].replace('_', ' ')
                    
                    # Add song details to the HTML list
                    status = "Now Playing" if is_current else "In Queue"
                    song_items.append(
                        f"""
                        <div class="song-card">
                            <div class="song-background" style="background-image: url('{thumbnail}');"></div>
                            <div class="song-overlay">
                                <div class="song-content">
                                    <div class="song-info">
                                        <h2 class="song-title">{song_name}</h2>
                                        <span class="song-status">{status}</span>
                                    </div>
                                    <div class="controls-container">
                                        <audio class="custom-audio-player" controls>
                                            <source src="{web_path}" type="audio/mpeg">
                                            Your browser does not support the audio element.
                                        </audio>
                                        <a href="{web_path}" download="{song_name}.mp3" 
                                        class="download-btn">
                                            <svg class="download-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                                            </svg>
                                            Download
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                    )
                    print(f"Added song to HTML: {song_name}")
                    
                except Exception as e:
                    print(f"Error processing song {song_data}: {e}")
                    continue

            # If no valid songs were added, show a message
            if not song_items:
                raise ValueError("No valid songs found to generate the HTML file")

            # Generate HTML content with pure CSS
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Tube Player</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
                    
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                        font-family: 'Poppins', sans-serif;
                    }}
                    
                    body {{
                        background: rgb(131,58,180);
                        background: linear-gradient(90deg, rgba(131,58,180,1) 0%, rgba(253,29,29,1) 50%, rgba(252,176,69,1) 100%);
                        min-height: 100vh;
                        padding: 2rem 1rem;
                    }}
                    
                    .container {{
                        max-width: 1024px;
                        margin: 0 auto;
                    }}
                    
                    .page-title {{
                        background: linear-gradient(90deg, #60a5fa, #3b82f6);
                        -webkit-background-clip: text;
                        background-clip: text;
                        color: transparent;
                        font-weight: 700;
                        letter-spacing: 0.05em;
                        text-transform: uppercase;
                        font-size: 2.25rem;
                        text-align: center;
                        margin-bottom: 2rem;
                    }}
                    
                    .song-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 1.5rem;
                        padding: 0 1rem;
                    }}
                    
                    .song-card {{
                        position: relative;
                        border-radius: 1rem;
                        overflow: hidden;
                        height: 200px;
                        transition: transform 0.3s ease;
                    }}
                    
                    .song-card:hover {{
                        transform: translateY(-5px);
                    }}
                    
                    .song-background {{
                        position: absolute;
                        inset: 0;
                        background-size: cover;
                        background-position: center;
                    }}
                    
                    .song-overlay {{
                        position: absolute;
                        inset: 0;
                        background: linear-gradient(180deg, 
                            rgba(0, 0, 0, 0.3) 0%,
                            rgba(0, 0, 0, 0.8) 100%);
                        display: flex;
                        align-items: flex-end;
                    }}
                    
                    .song-content {{
                        padding: 1.5rem;
                        width: 100%;
                    }}
                    
                    .song-info {{
                        margin-bottom: 1rem;
                    }}
                    
                    .song-title {{
                        color: white;
                        font-size: 1.25rem;
                        font-weight: 600;
                        margin-bottom: 0.25rem;
                    }}
                    
                    .song-status {{
                        color: #60a5fa;
                        font-size: 0.875rem;
                        font-weight: 500;
                    }}
                    
                    .controls-container {{
                        display: flex;
                        flex-direction: column;
                        gap: 0.75rem;
                    }}
                    
                    .custom-audio-player {{
                        width: 100%;
                        height: 36px;
                        border-radius: 0.5rem;
                    }}
                    
                    .custom-audio-player::-webkit-media-controls-panel {{
                        background: rgba(255, 255, 255, 0.1);
                    }}
                    
                    .custom-audio-player::-webkit-media-controls-play-button {{
                        background-color: #3b82f6;
                        border-radius: 50%;
                    }}
                    
                    .download-btn {{
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        padding: 0.5rem 1rem;
                        background: rgba(59, 130, 246, 0.8);
                        color: white;
                        border-radius: 0.5rem;
                        font-weight: 500;
                        text-decoration: none;
                        transition: background 0.2s ease;
                    }}
                    
                    .download-btn:hover {{
                        background: rgb(59, 130, 246);
                    }}
                    
                    .download-icon {{
                        width: 1.25rem;
                        height: 1.25rem;
                    }}
                    
                    footer {{
                        margin-top: 2rem;
                        text-align: center;
                        color: #9ca3af;
                        font-size: 0.875rem;
                    }}
                    
                    @media (max-width: 640px) {{
                        .page-title {{
                            font-size: 1.875rem;
                        }}
                        
                        .song-card {{
                            height: 250px;
                        }}
                        
                        .controls-container {{
                            gap: 1rem;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="page-title">Tube Player</h1>
                    <div class="song-grid">
                        {''.join(song_items)}
                    </div>
                    <footer>
                        <p>Made with ❤️ for music lovers</p>
                    </footer>
                </div>
                
                <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        const audioPlayers = document.querySelectorAll('audio');
                        
                        audioPlayers.forEach(player => {{
                            player.addEventListener('play', function() {{
                                audioPlayers.forEach(p => {{
                                    if (p !== player) {{
                                        p.pause();
                                    }}
                                }});
                            }});
                        }});
                    }});
                </script>
            </body>
            </html>
            """

            # Save HTML file
            html_path = os.path.join(self.html_dir, 'index.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("HTML file generated successfully!")
            return True

        except Exception as e:
            print(f"Error generating music player: {e}")
            return False