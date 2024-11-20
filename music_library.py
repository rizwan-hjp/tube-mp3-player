import flet as ft
from utils import format_duration
import math
def create_bottom_sheet(db, on_play_song, page, on_close, on_play_selected):
    selected_songs = []
    playlist_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Select")),
            ft.DataColumn(ft.Text("Title")),
            ft.DataColumn(ft.Text("Duration")),
            ft.DataColumn(ft.Text("Actions")),
        ],
        rows=[],
    )

    def handle_delete_song(song_id):
        db.delete_song(song_id)
        update_table()
        page.update()

    def handle_checkbox_change(e, file_path, thumbnail):
        if e.control.value:
            selected_songs.append((file_path, thumbnail))
        else:
            selected_songs.remove((file_path, thumbnail))
        play_selected_button.disabled = len(selected_songs) == 0
        page.update()

    def play_selected_songs():
        if selected_songs:
            on_play_selected(selected_songs)
            page.close(bottom_sheet)

    def update_table():
        playlist_table.rows.clear()
        songs = db.get_all_songs()
        selected_songs.clear()
        
        for song in songs:
            song_id, title, file_path, thumbnail, duration, _ = song
            
            checkbox = ft.Checkbox(
                value=False,
                on_change=lambda e, fp=file_path, tn=thumbnail: handle_checkbox_change(e, fp, tn)
            )
            
            # play_button = ft.IconButton(
            #     icon=ft.icons.PLAY_CIRCLE,
            #     icon_color=ft.colors.GREEN,
            #     data=file_path,
            #     tooltip="Play",
            #     on_click=lambda e, fp=file_path, tn=thumbnail: on_play_song(fp, tn)
            # )
            play_button = ft.Text('')

            
            delete_button = ft.IconButton(
                icon=ft.icons.DELETE,
                icon_color=ft.colors.RED,
                data=song_id,
                tooltip="Delete",
                on_click=lambda e, sid=song_id: handle_delete_song(sid)
            )

                        # Create the title widget with tooltip and ellipsis
            title_widget =ft.Text(
                title, 
                width=200,
                overflow=ft.TextOverflow.ELLIPSIS,
                tooltip=ft.Tooltip(
                message= title,
                padding=20,
                vertical_offset= -100,
                border_radius=10,
                text_style=ft.TextStyle(size=20, color=ft.colors.WHITE),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.Alignment(0.8, 1),
                    colors=[
                        "0xff1f005c",
                        "0xff5b0060",
                        "0xff870160",
                        "0xffac255e",
                        "0xffca485c",
                        "0xffe16b5c",
                        "0xfff39060",
                        "0xffffb56b",
                    ],
                    tile_mode=ft.GradientTileMode.MIRROR,
                    rotation=math.pi / 3,
                ),
            )
            )
            

            playlist_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(checkbox),
                        ft.DataCell(title_widget),
                        ft.DataCell(ft.Text(format_duration(duration))),
                        ft.DataCell(ft.Row([play_button, delete_button])),
                    ]
                )
            )

    play_selected_button = ft.ElevatedButton(
        "Play Selected",
        icon=ft.icons.PLAY_ARROW,
        on_click=lambda _: play_selected_songs(),
        disabled=True
    )

    def handle_on_dismiss():
        play_selected_button.disabled = True

    bottom_sheet = ft.BottomSheet(
            on_dismiss=lambda e: handle_on_dismiss(),
            content=ft.Container(
                expand=True,
                padding=20,
                bgcolor='#17202a',
                content=ft.Column(
                    [
                        ft.Row(
                            controls=[
                                ft.Text("Music Library", size=20, weight=ft.FontWeight.BOLD),
                                ft.IconButton(icon=ft.icons.CLOSE, on_click=on_close),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[play_selected_button],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[playlist_table],  # Add playlist_table to ListView for scrolling
                                expand=True,
                                auto_scroll=True,  # Automatically scroll to the end if new items are added
                            ),
                            expand=True,  # Ensure it takes up all available space
                        ),
                    ],
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
            ),
        )



    bottom_sheet.update_table = update_table
    return bottom_sheet