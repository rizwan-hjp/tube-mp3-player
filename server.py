import flet as ft
import qrcode
import base64
from io import BytesIO
import os
import socket
from threading import Thread
from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn
import logging
import time  # For polling

# Initialize FastAPI
app = FastAPI()

# Directory containing the song and HTML files
song_directory = "./assets"
song_filename = "example.mp3"  # Replace with your song's filename
port = 8000  # Port for the HTTP server

# Variable to track the dialog close event
close_dialog_flag = False

# Check if the song file exists
def check_song_file():
    song_path = os.path.join(song_directory, song_filename)
    if not os.path.exists(song_path):
        print(f"Error: {song_path} not found!")
    else:
        print(f"Found the song file at {song_path}")

check_song_file()

# Serve the song file through FastAPI
@app.get("/song")
async def serve_song():
    song_path = os.path.join(song_directory, song_filename)
    print(f"Serving song from: {song_path}")  # Debugging line
    return FileResponse(song_path)

# Serve the HTML page through FastAPI
@app.get("/")
async def serve_html():
    html_filename = f"{os.path.splitext(song_filename)[0]}.html"
    html_path = os.path.join(song_directory, html_filename)
    print(f"Serving HTML page from: {html_path}")  # Debugging line
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        return {"message": "HTML page not found"}

# Get the local IP address of the machine
def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

# Start FastAPI server in a separate thread
def start_http_server():
    local_ip = get_local_ip()
    print(f"Serving at http://{local_ip}:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", loop="asyncio")

# Generate HTML page to play the song with QR code and close button
def generate_html_page(song_filename, output_path):
    local_ip = get_local_ip()
    song_url = f"http://{local_ip}:{port}/song"  # URL for song
    song_name = os.path.splitext(song_filename)[0]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{song_name} - Music Player</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .audio-player {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .close-btn {{
                background-color: #e11d48;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                cursor: pointer;
                text-align: center;
            }}
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <div class="max-w-md mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
                <div class="audio-player p-6 text-white">
                    <div class="text-center mb-4">
                        <h1 class="text-2xl font-bold">{song_name}</h1>
                    </div>
                    <audio controls class="w-full mb-4" preload="metadata">
                        <source src="{song_url}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    <a href="{song_url}" download 
                       class="block w-full bg-white text-indigo-600 text-center py-3 rounded-lg font-bold hover:bg-indigo-50 transition duration-300">
                        <i class="fas fa-download mr-2"></i>Download Song
                    </a>
                </div>
            </div>
        </div>

        <!-- Close button to close the tab in the mobile browser -->
        <div class="text-center mt-4">
            <button class="close-btn" onclick="closeWindow()">Close</button>
        </div>

        <script>
            // Function to close the window and notify the server
            function closeWindow() {{
                fetch('/close', {{ method: 'POST' }}).then(response => response.json()).then(data => {{
                    console.log(data.message);
                    window.close();  // Close the window after notifying the server
                }}).catch(error => {{
                    console.error("Error closing window:", error);
                }});
            }}
        </script>
    </body>
    </html>
    """

    # Write the HTML content to the file
    with open(output_path, "w") as f:
        f.write(html_content)

# New route to handle close button click event
@app.post("/close")
async def handle_close_button():
    global close_dialog_flag
    print("Close button clicked!")  # Logs the event when the close button is clicked
    close_dialog_flag = True  # Set the flag to True when the close button is clicked
    return {"message": "Close button clicked"}

# Main Flet App
def main(page: ft.Page):
    page.title = "Play Song with QR Code"

    # Initialize the dialog object
    page.dialog = None

    # Start the FastAPI server in a separate thread
    Thread(target=start_http_server, daemon=True).start()

    # Generate QR Code
    def generate_qr_code():
        local_ip = get_local_ip()
        song_url = f"http://{local_ip}:{port}/song"  # Ensure this points to /song

        # Generate the QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(song_url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        # Convert QR code to base64 for Flet Image
        qr_buffer = BytesIO()
        img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")
        return qr_base64

    # Toggle QR Code Dialog
    def show_qr_code(e):
        global close_dialog_flag  # Ensure it's accessible
        # Check if the dialog is already open
        if page.dialog and page.dialog.open:
            # If the dialog is open, close it
            page.dialog.open = False
            page.update()
        else:
            # If the dialog is closed, show the QR code
            qr_base64 = generate_qr_code()
            qr_image = ft.Image(src_base64=qr_base64, width=300, height=300)
            
            page.dialog = ft.AlertDialog(
                title=ft.Text("Scan to Play Song"),
                content=qr_image,
                actions=[
                    ft.TextButton("Close", on_click=lambda _: dialog_Status())
                ],  # Close button to hide the dialog
            )
            page.dialog.open = True
            page.update()

    # Function to close the dialog
    def dialog_Status():


        print("QR Code dialog closed.")  # Log to terminal
  
        show_qr_code(None)


    # Polling to check if the FastAPI server triggered the close event
    def check_close_event():
        global close_dialog_flag
        while True:
            if close_dialog_flag:
                dialog_Status()  # Close the dialog when the flag is True
                close_dialog_flag = False  # Reset the flag
            time.sleep(1)

    # Start the polling in a separate thread
    Thread(target=check_close_event, daemon=True).start()

    # Floating Action Button
    fab = ft.FloatingActionButton(
        icon=ft.icons.QR_CODE,
        bgcolor=ft.colors.BLUE,
        on_click=show_qr_code,
    )

    # Add Floating Action Button
    page.add(
        ft.Stack(
            [
                ft.Text("Click the QR button to share the song with your mobile."),
                ft.Container(
                    fab,
                    alignment=ft.alignment.bottom_right,
                    margin=ft.margin.all(16),
                ),
            ],
            expand=True,
        )
    )

    # Generate the HTML page for the song
    html_output_path = f"./assets/{os.path.splitext(song_filename)[0]}.html"
    generate_html_page(song_filename, html_output_path)
    print(f"Generated HTML page: {html_output_path}")

ft.app(target=main)