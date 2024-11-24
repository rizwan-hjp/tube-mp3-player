import flet as ft
import qrcode
import io
import base64

class ShareAndFeedback(ft.UserControl):
    def __init__(self, share_url: str, feedback_url: str):
        super().__init__()
        self.share_url = share_url
        self.feedback_url = feedback_url
        self.qr_base64 = self.generate_qr_code()
        
    def generate_qr_code(self):
        """Generate QR code and convert to base64."""
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(self.share_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def show_share_options(self, e):
        """Show sharing options dialog."""
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Share Via"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(name=ft.icons.SHARE, color="green"),
                                ft.Text("WhatsApp")
                            ]),
                            on_click=lambda _: self.page.launch_url(f"whatsapp://send?text={self.share_url}")
                        ),
                    ]),
                    ft.Row([
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(name=ft.icons.SEND, color="blue"),
                                ft.Text("Telegram")
                            ]),
                            on_click=lambda _: self.page.launch_url(f"tg://msg?text={self.share_url}")
                        ),
                    ]),
                    ft.Row([
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(name=ft.icons.EMAIL, color="red"),
                                ft.Text("Email")
                            ]),
                            on_click=lambda _: self.page.launch_url(f"mailto:?body={self.share_url}")
                        ),
                    ]),
                    # ft.Row([
                    #     ft.TextButton(
                    #         content=ft.Row([
                    #             ft.Icon(name=ft.icons.MESSAGE, color="orange"),
                    #             ft.Text("SMS")
                    #         ]),
                    #         on_click=lambda _: self.page.launch_url(f"sms:?body={self.share_url}")
                    #     ),
                    # ]),
                    ft.Row([
                        ft.TextButton(
                            content=ft.Row([
                                ft.Icon(name=ft.icons.QR_CODE, color="white"),
                                ft.Text("QR Code")
                            ]),
                            on_click=self.show_qr_code
                        ),
                    ]),
                ], tight=True),
                padding=10
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog())
            ],
        )
        self.page.dialog.open = True
        self.page.update()

    def show_qr_code(self, e):
        """Show QR code in a dialog."""
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Scan QR Code"),
            shadow_color="red",
            content=ft.Column(
                controls=[
                    ft.Image(src_base64=self.qr_base64, width=200, height=200),
                    ft.Text("Share Tube Player on Mobile", size=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                height=self.page.height * 0.5,
                width=300
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: self.close_dialog())],
        )
        self.page.dialog.open = True
        self.page.update()

    def close_dialog(self):
        """Close the dialog"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def open_feedback(self, e):
        """Open feedback URL"""
        self.page.launch_url(self.feedback_url)

    def build(self):
        # Share button with an icon
        share_button = ft.IconButton(
            icon=ft.icons.SHARE,
            tooltip="Share Tube Player",
            on_click=self.show_share_options,
        )

        # Feedback button with an icon
        feedback_button = ft.IconButton(
            icon=ft.icons.FEEDBACK,
            tooltip="Give Feedback",
            on_click=self.open_feedback,
        )

        return ft.Row(
            controls=[
                share_button,
                feedback_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )