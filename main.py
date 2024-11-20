import flet as ft
from database import Database
from audio_player import AudioPlayer
from youtube_downloader import YouTubeDownloader
import threading
import os
from time import sleep
from music_library import create_bottom_sheet
from queueManager import QueueManager
import ctypes
from titleBar import TitleBar
from sharemusic import ShareMusic

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1E1E1E"  # Replace with your desired theme color
    # page.window_frameless = True
    page.window_title_bar_hidden = True
    # Get screen resolution
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    # Calculate position to center the window
    page.window_left = (screen_width - page.window_width) // 2
    page.window_top = (screen_height - page.window_height) // 2
    page.title = "Tube Player"   
    page.window_width = 1175
    page.window_height=660
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    page.spacing = 0
    page.window_resizable = True

    # Create the TitleBar widget
    title_bar = TitleBar(page)

    bottom_sheet = ft.BottomSheet(content=ft.Text("Waiting for download..."))
    page.add(bottom_sheet)
    db = Database()
    audio_player = AudioPlayer()
    youtube_downloader = YouTubeDownloader(bottom_sheet)
    queue_manager = QueueManager()
    download_cancel_flag = threading.Event()  # Add cancel flag
    remaining_time_text = ft.Text("00:00", size=16, color=ft.colors.GREEN)
    shareMusic = ShareMusic(page,audio_player,queue_manager,db)

    # add code
    # Add new controls for loop and seeking
    seek_slider = ft.Slider(
        min=0,
        max=100,
        value=0,
        label="Position",
        width=400,
        active_color=ft.colors.GREEN,
    )

    current_time_text = ft.Text("00:00", size=14)
    total_time_text = ft.Text("00:00", size=14)

    loop_button = ft.IconButton(
        icon=ft.icons.REPEAT, icon_color=ft.colors.GREY, icon_size=24, tooltip="No Loop"
    )

    def format_time(seconds):
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def update_loop_button():
        if queue_manager.loop_mode == "no_loop":
            loop_button.icon_color = ft.colors.GREY
            loop_button.tooltip = "No Loop"
        elif queue_manager.loop_mode == "loop_one":
            loop_button.icon_color = ft.colors.GREEN
            loop_button.tooltip = "Loop One"
        else:  # loop_all
            loop_button.icon_color = ft.colors.BLUE
            loop_button.tooltip = "Loop All"
        page.update()

    def toggle_loop(e):
        modes = ["no_loop", "loop_one", "loop_all"]
        current_index = modes.index(queue_manager.loop_mode)
        queue_manager.loop_mode = modes[(current_index + 1) % len(modes)]
        update_loop_button()
        # Update next button state based on loop mode
        next_button.disabled = not queue_manager.has_next_song()
        page.update()

    loop_button.on_click = toggle_loop

    def on_seek_change(e):
        if audio_player.current_file:
            position = (e.control.value / 100) * total_duration
            audio_player.seek(position)
            audio_player.resume()

    def on_drag(e):
        audio_player.pause()
        print("focus")

    seek_slider.on_change_start = on_drag
    # seek_slider.on_blur = on_blur

    seek_slider.on_change_end = on_seek_change

    def on_position_update(position):
        """Update the UI components based on the current playback position."""

        if audio_player.current_file:
            # Update the seek slider value based on the current position
            seek_slider.value = (
                (position / total_duration) * 100 if total_duration > 0 else 0
            )
            current_time_text.value = format_time(position)

            # Calculate and update the remaining time
            remaining_time = total_duration - position
            remaining_time_text.value = f"Remaining: {format_time(remaining_time)}"
            total_time_text.value = format_time(remaining_time)
        else:
            # Reset UI components when no file is playing
            seek_slider.value = 0
            current_time_text.value = "00:00"
            remaining_time_text.value = "Remaining: 00:00"

        # Ensure UI updates are reflected
        page.update()

    def on_duration(duration):
        global total_duration
        total_duration = duration
        # total_time_text.value = format_time(duration)

    # add code

    # Update play_next_song function to handle looping
    def play_next_song():
        next_song = queue_manager.get_next_song()
        if next_song:
            file_path, thumbnail = next_song
            handle_play_song(file_path, thumbnail)
        else:
            playing_status_text.value = "End of queue."
            play_button.icon = ft.icons.PLAY_ARROW
            now_playing_text.value = ""
            stop_button.disabled = True
            next_button.disabled = True
            prev_button.disabled = True
            page.update()

    # Update the song completion callback
    def on_song_complete():
        if queue_manager.has_next_song():
            play_next_song()
        else:
            playing_status_text.value = "Playback completed!"
            play_button.icon = ft.icons.PLAY_ARROW
            now_playing_text.value = ""
            stop_button.disabled = True
            next_button.disabled = True
            prev_button.disabled = True
            seek_slider.value = 0
        page.update()

    # Update your existing callbacks
    audio_player.set_on_complete_callback(on_song_complete)
    audio_player.set_on_duration_callback(on_duration)
    audio_player.set_on_position_update_callback(on_position_update)

    background_image = ft.Image(
        src="./assets/app_bg.png",
        fit=ft.ImageFit.COVER,
        expand=True,
        opacity=0.3,
        border_radius=5,
    )

    background_container = ft.Container(
        content=background_image,
        alignment=ft.alignment.center,
        expand=True,
        padding=0,
    )

    url_input = ft.TextField(
        label="YouTube URL",
        hint_text="Paste YouTube URL here...",
        width=500,
        bgcolor=ft.colors.SURFACE_VARIANT,
    )

    progress_bar = ft.ProgressBar(width=500, visible=False)
    download_status_text = ft.Text()
    playing_status_text = ft.Text()
    video_title = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    now_playing_text = ft.Text("", size=16, color=ft.colors.GREEN)

    play_button = ft.IconButton(
        icon=ft.icons.PLAY_ARROW,
        disabled=True,
        icon_color=ft.colors.GREEN,
        icon_size=32,
    )

    stop_button = ft.IconButton(
        icon=ft.icons.STOP, disabled=True, icon_color=ft.colors.RED, icon_size=32
    )

    prev_button = ft.IconButton(
        icon=ft.icons.SKIP_PREVIOUS,
        disabled=True,
        icon_color=ft.colors.BLUE,
        icon_size=32,
    )

    next_button = ft.IconButton(
        icon=ft.icons.SKIP_NEXT, disabled=True, icon_color=ft.colors.BLUE, icon_size=32
    )

    volume_slider = ft.Slider(
        min=0,
        max=100,
        value=50,
        label="Volume",
        width=200,
    )

    def on_volume_change(e):
        volume = e.control.value / 100
        audio_player.set_volume(volume)

    volume_slider.on_change = on_volume_change

    control_row = ft.Row(
        [
            prev_button,
            play_button,
            stop_button,
            next_button,
            loop_button,
            ft.Container(width=20),
            ft.Icon(name=ft.icons.VOLUME_UP),
            volume_slider,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # Add seeking controls row
    seeking_row = ft.Row(
        [current_time_text, seek_slider, total_time_text],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # Update bottom_container to include seeking controls
    bottom_container = ft.Container(
        content=ft.Column(
            [now_playing_text, seeking_row, control_row],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.bottom_center,
        padding=10,
    )

    def handle_play_song(file_path, thumbnail):
  
        song_info = db.get_song_by_path(file_path)
      
        if song_info:
            now_playing_text.value = f"Now Playing: {song_info[1]}"
        background_image.src = thumbnail
        page.update()

        if audio_player.play(file_path):
            play_button.icon = ft.icons.PAUSE
            play_button.disabled = False
            stop_button.disabled = False
            next_button.disabled = (
                len(queue_manager.queue) <= 1
                or queue_manager.current_index >= len(queue_manager.queue) - 1
            )
            prev_button.disabled = queue_manager.current_index <= 0
            playing_status_text.value = "Playing..."
            
            page.update()
        else:
            playing_status_text.value = "Error playing audio"
            page.update()

    def handle_play_selected(selected_songs):
        queue_manager.clear_queue()
        queue_manager.add_songs(selected_songs)
        first_song = queue_manager.get_current_song()
        if first_song:
            file_path, thumbnail = first_song
            handle_play_song(file_path, thumbnail)

    bs = create_bottom_sheet(
        db,
        handle_play_song,
        page,
        on_close=lambda e: page.close(bs),
        on_play_selected=handle_play_selected,
    )

    def open_bottom_sheet(e):
        bs.update_table()
        page.open(bs)
        page.update()

    def play_audio(e):
        current_song = queue_manager.get_current_song()
        if current_song:
            file_path, _ = current_song
            if audio_player.current_file and os.path.exists(file_path):
                if not audio_player.playing:
                    if audio_player.paused:
                        audio_player.resume()
                    else:
                        success = audio_player.play(file_path)
                        if not success:
                            playing_status_text.value = "Error playing audio"
                            page.update()
                            return
                    play_button.icon = ft.icons.PAUSE
                    playing_status_text.value = "Playing..."
                else:
                    audio_player.pause()
                    play_button.icon = ft.icons.PLAY_ARROW
                    playing_status_text.value = "PAUSE"
                page.update()

    def stop_audio(e):
        audio_player.stop()
        play_button.icon = ft.icons.PLAY_ARROW
        queue_manager.clear_queue()
        next_button.disabled = True
        prev_button.disabled = True
        now_playing_text.value = ""
        page.update()

    def handle_next(e):
        play_next_song()

    def handle_previous(e):
        if queue_manager.current_index > 0:
            queue_manager.current_index -= 2
            play_next_song()

    play_button.on_click = play_audio
    stop_button.on_click = stop_audio
    next_button.on_click = handle_next
    prev_button.on_click = handle_previous

    def update_progress(progress):
        if download_cancel_flag.is_set():
            raise Exception("Download cancelled")
        progress_bar.value = progress / 100
        page.update()

    def download_thread(url):
        try:
            progress_bar.visible = True
            download_status_text.value = "Getting video info..."
            page.update()

            info = youtube_downloader.get_video_info(url)

            if download_cancel_flag.is_set():

                youtube_downloader.cancel_download()
                raise Exception("Download cancelled")

            def close_dialog(e):
                rename_dialog.open = False
                page.update()

            def confirm_rename(e):
                nonlocal custom_title
                custom_title = title_field.value
                rename_dialog.open = False
                page.update()
                continue_download()

            custom_title = info["original_title"]
            title_field = ft.TextField(
                value=info["original_title"], label="Enter custom title", width=400
            )

            rename_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Rename Download"),
                bgcolor="#17202a",
                content=ft.Column(
                    [
                        ft.Container(height=20),
                        ft.Text("Original title: " + info["original_title"]),
                        ft.Container(height=20),
                        title_field,
                    ]
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.TextButton("Confirm", on_click=confirm_rename),
                ],
                actions_alignment="end",
            )

            page.dialog = rename_dialog
            rename_dialog.open = True
            page.update()

            def continue_download():
                if download_cancel_flag.is_set():
                    return

                download_status_text.value = "Downloading and converting..."
                page.update()

                file_path = youtube_downloader.download(url, update_progress)

                if os.path.exists(file_path):
                    db.add_song(
                        custom_title, file_path, info["thumbnail"], info["duration"]
                    )

                    download_status_text.value = "Ready to play!"
                    play_button.disabled = False
                    stop_button.disabled = False
                    # Clear URL field after successful download
                    url_input.value = ""

                    page.update()
                    download_complited()
                else:
                    raise Exception(f"File not found: {file_path}")

        except Exception as e:
            if str(e) == "Download cancelled":
                download_status_text.value = "Download cancelled"
            else:
                download_status_text.value = f"Error: {str(e)}"
            play_button.disabled = True
            stop_button.disabled = True
        finally:
            progress_bar.visible = False
            url_input.disabled = False
            download_cancel_flag.clear()  # Reset cancel flag
            download_button.text = "Download"  # Reset button text
            download_button.style.bgcolor = {ft.MaterialState.DEFAULT: ft.colors.BLUE}
            page.update()

    def download_complited():
        sleep(5)
        download_status_text.value = ""
        page.update

    def handle_download_button(e):
        if download_button.text == "Download":
            if not url_input.value:
                download_status_text.value = "Please enter a YouTube URL"
                page.update()
                return

            url_input.disabled = True
            download_button.text = "Cancel Download"
            download_button.style.bgcolor = {ft.MaterialState.DEFAULT: ft.colors.RED}
            download_cancel_flag.clear()
            threading.Thread(
                target=download_thread, args=(url_input.value,), daemon=True
            ).start()
        else:
            # Cancel download
            download_cancel_flag.set()
            download_status_text.value = "Cancelling download..."
            page.update()

    download_button = ft.ElevatedButton(
        "Download",
        on_click=handle_download_button,
        style=ft.ButtonStyle(
            color={ft.MaterialState.DEFAULT: ft.colors.WHITE},
            bgcolor={ft.MaterialState.DEFAULT: ft.colors.BLUE},
        ),
    )




    page.add(
        ft.Stack(
            expand=True,
            
            controls=[
                background_container,
                 title_bar,
                ft.Column(
                    [
                       
                        ft.Text("Tube Player", size=30, weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        ft.Row(
                            [url_input, download_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Container(height=20),
                        progress_bar,
                        download_status_text,
                        playing_status_text,
                        ft.Container(height=10),
                        # remaining_time_text,
                        video_title,
                        ft.Container(height=20),
                        bottom_container,
                        ft.ElevatedButton("Music Library", on_click=open_bottom_sheet),
                        shareMusic.musicShareButton
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
            ],
        )
    )

    def page_cleanup():
        audio_player.stop()
        db.conn.close()

    page.on_close = page_cleanup


if __name__ == "__main__":
    ft.app(target=main)
