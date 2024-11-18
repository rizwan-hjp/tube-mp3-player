import flet as ft

class PayPalDonation(ft.UserControl):
    def __init__(self, button_url: str):
        super().__init__()
        self.button_url = button_url

    def build(self):
        # Function to open PayPal donation link in the user's default browser
        def open_paypal_donation(e):
            self.page.launch_url(self.button_url)  # Open the donation URL in the default browser

        # PayPal donation button
        paypal_button = ft.ElevatedButton(
            text="Donate via PayPal",
            icon=ft.icons.PAYMENTS,
            on_click=open_paypal_donation,  # Trigger the donation link when clicked
        )

        # Return the layout with a message and the donation button
        return ft.Column(
            controls=[
                paypal_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )