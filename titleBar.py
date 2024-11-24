import flet as ft
from PayPalDonation import PayPalDonation
from shareAndFeedback import ShareAndFeedback

class TitleBar(ft.Container):

 
        
    def __init__(self, page, **kwargs):
        super().__init__(**kwargs)
        self.page = page
        # self.theme_color = "#202124c4"
        self.theme_color ="transparent"
        self.donation_component = PayPalDonation(
            button_url="https://www.paypal.com/paypalme/donation4happiness",  # Replace with your hosted donation page
            )
        self.shareandfeedback = ShareAndFeedback(
             share_url="https://tubeplayer-desk.web.app/",
             feedback_url="https://tubeplayer-desk.web.app/",
            )
    
        # Window Control Functions
        def minimize_window(_):
            """Minimize the window."""
            self.page.window_minimized = True
            self.page.update()

        def maximize_restore_window(_):
            """Toggle maximize/restore window."""
            self.page.window_maximized = not self.page.window_maximized
            self.page.update()

        def close_window(_):
            """Close the window."""
            self.page.window_close()
        
        def handle_logo(_):
            
            about_dialog = ft.AlertDialog(
                    title=ft.Text("About"),
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "This app is a versatile utility application designed for personal use "
                                "and entertainment. It combines productivity tools with engaging features "
                                "to make your experience seamless and enjoyable.",
                                selectable=True,
                                size=14,
                            ),
                            ft.Text(
                                "Key Features:\n"
                                "1. Easy-to-use interface.\n"
                                "2. Customizable utilities.\n"
                                "3. Designed for personal productivity and fun.",
                                selectable=True,
                                size=14,
                            ),
                            ft.Text(
                                "\nThank you for using our app!",
                                size=14,
                                italic=True,
                            ),
                            # New section for donation and improvement
                            ft.Text(
                                "\nDonate for Improvement:",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Your donations help us improve the app and provide better features "
                                "for a seamless user experience. Please consider donating to support our work!",
                                size=14,
                                selectable=True,
                            ),
                           self.donation_component,
                           self.shareandfeedback,
                           
                        ]
                    ),
                    actions=[
                        ft.TextButton("Close", on_click=lambda e: close_about_dialog())
                    ],
                    shape=ft.RoundedRectangleBorder(radius=0),  # No border radius
                )
            
            # Show the dialog
            page.dialog = about_dialog
            about_dialog.open = True
            page.update()

        def close_about_dialog():
            # Close the dialog
            page.dialog.open = False
            page.update()  
        
        
      
            
        # Define app title (with logo)
        app_title = ft.Container(
            bgcolor=self.theme_color,
            height=40,
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Image(src="assets/app_icon.ico", width=30, height=30),  # Logo
                        width=40,  # Container width to hold the logo
                        padding=ft.padding.only(10, 0, 0, 0),
                        on_click= handle_logo
                    ),
                    ft.Container(
                        content=ft.Text("Tube Player", size=16, weight=ft.FontWeight.BOLD, color="white"),
                        expand=True  # This ensures the text fills up available space
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.donation_component,
                                self.shareandfeedback
                            ]
                        ) 
                    )
                ],
            ),
        )

        # Define title bar
        self.content = ft.Container(
            bgcolor=self.theme_color,
            height=40,
            content=ft.Row(
                controls=[
                    ft.WindowDragArea(  # Make the title bar draggable
                        content=ft.Row(
                            controls=[app_title],
                            expand=True,
                        ),
                        expand=True,
                    ),
                    ft.IconButton(icon=ft.icons.MINIMIZE, icon_color="white", on_click=minimize_window),
                    ft.IconButton(icon=ft.icons.CROP_SQUARE, icon_color="white", on_click=maximize_restore_window),
                    ft.IconButton(icon=ft.icons.CLOSE, icon_color="white", on_click=close_window),
                ],
                spacing=0,
            ),
        )
