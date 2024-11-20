import qrcode
from io import BytesIO
import base64
import socket
from threading import Thread
from flask import Flask, send_from_directory, send_file
import os

# Flask app setup
app = Flask(__name__)

# Global variables
html_dir = os.path.join(os.getcwd(), "html")
port = 8000

# Ensure the 'html' directory exists
os.makedirs(html_dir, exist_ok=True)

def get_ip_address():
    """Get the first available non-loopback IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error fetching IP address: {e}")
        return "127.0.0.1"

def generate_qr_code(port):
    """Generate QR code for the server URL."""
    ip_address = get_ip_address()
    url = f"http://{ip_address}:{port}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8"), ip_address

@app.route("/")
def serve_html():
    """Serve the music player HTML."""
    try:
        return send_from_directory(html_dir, 'index.html')
    except Exception as e:
        print(f"Error serving HTML: {e}")
        return "Error loading music player", 500

@app.route("/<path:filename>")
def serve_file(filename):
    """Serve any file from the html directory."""
    try:
        return send_from_directory(html_dir, filename)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return f"Error serving file: {filename}", 404

def clean_html_dir():
    """Clean up the html directory before starting."""
    if os.path.exists(html_dir):
        for file in os.listdir(html_dir):
            file_path = os.path.join(html_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

def start_flask_server():
    """Start the Flask server in a separate thread."""
    # Clean up old files
    clean_html_dir()
    
    # Create html directory if it doesn't exist
    os.makedirs(html_dir, exist_ok=True)
    
    # Start the server
    Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False), daemon=True).start()