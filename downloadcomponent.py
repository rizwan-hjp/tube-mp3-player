import flet as ft

class DownloadComponent:
    def __init__(self, button_text="Download", on_click_callback=None, hint_text="Enter URL"):
        # Set default values or use provided values
        self.button_text = button_text
        self.on_click_callback = on_click_callback or self.default_callback
        self.hint_text = hint_text

    def default_callback(self, e):
        print("Download button clicked")
        print("Input URL:", self.input_field.value)

    def create_input_and_button(self):
        # Create an input field with hint_text
        self.input_field = ft.TextField(
            label="Enter URL",
            hint_text=self.hint_text,
            autofocus=True,
            width=300  # Optional: adjust the width of the input field
        )

        # Create the download button
        download_button = ft.ElevatedButton(
            self.button_text,
            on_click=self.on_click_callback,
            style=ft.ButtonStyle(
                color={ft.MaterialState.DEFAULT: ft.colors.WHITE},
                bgcolor={ft.MaterialState.DEFAULT: ft.colors.BLUE},
            ),
        )

        # Arrange the input field and button in a single line using Row
        return ft.Row([self.input_field, download_button])

