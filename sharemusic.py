import flet as ft
import os
import qr_code_server
import shutil
from urllib.parse import quote
import pathlib
from  firewallManager import FirewallManager
import base64
class ShareMusic:
    def __init__(self, page, audio_player, queue_manager, db):
        self.page = page
        self.single_play = audio_player
        self.db = db
        self.queue_manager = queue_manager
        self.firewall_manager = FirewallManager()
        # self.port = 8000
        # self.firewall_checker = FirewallCheck(self.port)
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
                on_click=self.isfirewall_added,
            ),
            alignment=ft.alignment.bottom_right,
            margin=ft.margin.all(16),
        )
    
    def add_firewall_rul(self, e, banner, rule_count):
        # Get the current working directory and join with 'tube player.exe'
        current_dir = os.getcwd()  # Get current working directory
        app_path = os.path.join(current_dir, 'tube player.exe')  # Join current directory with 'tube player.exe'
        # app_path = r"C:\users\dell\appdata\local\programs\tube player\tube player.exe"
        app_name = f'tube player.exe'
        
        # Remove the banner from the page
        self.page.close(banner)
        self.page.update()

        # Try to add firewall rule
        status = self.firewall_manager.add_firewall_rule(app_name, app_path, rule_count)
     
        
        # If status is False, show dialog about running as admin
        if not status:
            # Create an alert dialog for admin rights
            # Create a medium-sized admin rights dialog with full detailed text
            self.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    "⚠️ Admin Rights Needed",
                    color=ft.colors.AMBER_400,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(
                                name=ft.icons.ADMIN_PANEL_SETTINGS,
                                color=ft.colors.BLUE_400,
                                size=24
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "The application needs to be run as an administrator to add firewall rules.",
                                    color=ft.colors.WHITE,
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                                expand=True,
                            )
                        ], 
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                        expand=True),
                        ft.Text(
                            "Please right-click on the application and select 'Run as administrator'.",
                            color=ft.colors.WHITE70,
                            size=13,
                            text_align=ft.TextAlign.LEFT,
                        ),
                    ], 
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.START),
                    width=400,  # Increased width for longer text
                    height=100,  # Increased height for two lines
                    padding=ft.padding.symmetric(horizontal=20, vertical=15)
                ),
                actions=[
                    ft.Container(
                        content=ft.ElevatedButton(
                            "Got it",
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_400,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8)
                            ),
                            on_click=lambda e: self.page.close(self.dialog)
                        ),
                        padding=ft.padding.only(bottom=15)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
                bgcolor=ft.colors.GREY_900,
                title_padding=ft.padding.symmetric(vertical=15),
                content_padding=ft.padding.all(0),
                shape=ft.RoundedRectangleBorder(radius=8)
            )
            
            # Set and open the dialog
            self.page.open(self.dialog)
            self.page.update()
        
        else:
            # Create a compact, dark-themed success dialog
            self.dialog = ft.AlertDialog(
                title=ft.Text(
                    "Firewall Rule Added!", 
                    color=ft.colors.GREEN_300,
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                content=ft.Row([
                    ft.Icon(
                        name=ft.icons.CHECK_CIRCLE_ROUNDED, 
                        color=ft.colors.GREEN_300,
                        size=30
                    ),
                    ft.Text(
                        "Good luck & Enjoy!", 
                        color=ft.colors.WHITE70,
                        size=14
                    )
                ], 
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10),
                actions=[
                    ft.TextButton(
                        "Close", 
                        on_click=lambda e: self.page.close(self.dialog)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                bgcolor=ft.colors.GREY_900,
                title_padding=10,
                content_padding=10,
                shape=ft.RoundedRectangleBorder(radius=8)
            )
            
            # Set and open the dialog
            self.page.open(self.dialog)
            self.page.update()

            
    def isfirewall_added(self, e):

        self.rule = self.firewall_manager.check_firewall_rule('tube player.exe')
       
        if not self.rule == True:


            self.banner = ft.Banner(
                bgcolor=ft.colors.AMBER_100,
                leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=40),
                content=ft.Text(
                    value="Firewall rule for 'Tube Player' is not added. Music cannot be played or downlaod on your mobile device.",
                    color=ft.colors.BLACK,
                    weight=ft.FontWeight.BOLD,
                    size=16
                ),
                actions=[
                    ft.TextButton(text="Yes, I want", on_click=lambda e: self.add_firewall_rul(e,self.banner,self.rule),style=ft.ButtonStyle(color='Green')),
                    ft.TextButton(text="cancel", on_click=lambda e: self.page.close(self.banner),style=ft.ButtonStyle(color='red') ),
                    # Optionally, you can add other actions like "Ignore" or "Cancel" here
                ],
            )
            self.page.open(self.banner)  # Use `add` to display the banner
            self.page.update()

            # print(self.firewall_manager.check_firewall_rule('tube player.exe'))
            return

        self.show_qr_code(e)  # If firewall rule is added, proceed to show the QR code



        

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
                    #  ft.Text(self.firewall_checker.check_firewall_status())
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
                        # Replace backslashes with forward slashes

                    with open(thumbnail, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                    # Create the data URI
                    data_uri = f"data:image/jpeg;base64,{base64_image}"                
                    # Add song details to the HTML list
                    status = "Now Playing" if is_current else "In Queue"
                    song_items.append(
                        f"""
                        <div class="song-card">
                            <div class="song-background" style="background-image: url('{data_uri}');"></div>
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