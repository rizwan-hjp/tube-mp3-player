import math
import flet as ft


def main(page: ft.Page):
    page.add(
        ft.Text("Hover to see the simple tooltip", tooltip="This is a simple tooltip"),
        ft.Text(
            value="Hover to see the complex tooltip",
            tooltip=ft.Tooltip(
                message="This is a complex tooltip",
                padding=20,
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
            ),
        ),
    )


ft.app(main)