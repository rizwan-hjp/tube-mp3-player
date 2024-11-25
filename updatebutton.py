import flet as ft
import subprocess

import ctypes
import time
import httpx
import asyncio
import os
import tempfile
import traceback


from appupdate import get_latest_release


class UpdateButton(ft.Container):
    def __init__(self, page: ft.Page, current_version: str = "3.1.1", **kwargs):
        super().__init__(**kwargs)
        self.page = page
        self.current_version = current_version
        self.text = ft.Text('A new version is available')

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Update Available"),  # Ensure title is a `ft.Text` object
            content=ft.Column(
                controls=[
                    ft.Text(f"Current version: {self.current_version}"),
                    self.text
                ],
                spacing=10,
                width=300,
                height=150
            ),
            actions=[
                ft.TextButton("Update", on_click=lambda e: self.start_update(self.dialog)),
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shadow_color='red'
        )

    async def check_for_updates(self):
        """Check for updates asynchronously."""
        try:
            self.new_version = await get_latest_release()
            self.data_list = list(self.new_version)

            if len(self.data_list) != 2:
                raise ValueError("Input must contain exactly two items")

            self.url_item = next((item for item in self.data_list if item.startswith('http')), None)
            if not self.url_item:
                raise ValueError("No valid URL found in input")

            self.version_item = next(item for item in self.data_list if item != self.url_item)
            # print(f"URL: {self.url_item}, Version: {self.version_item}")

            current_version_tuple = tuple(map(int, self.current_version.split('.')))
            new_version_tuple = tuple(map(int, self.version_item.split('.')))
            if new_version_tuple > current_version_tuple:
                self.show_update_dialog(self.url_item, self.version_item)

        except Exception as e:
            # print(f"Error checking for updates: {str(e)}")
            pass

    def show_update_dialog(self, url_item, version_item):
        update_content = ft.Column(
            controls=[
                ft.Text(f"A new version {version_item} is available.\n"
                        f"Current version: {self.current_version}"),  # Correct use of ft.Text
                ft.ProgressBar(visible=False, width=300)
            ],
            spacing=20
        )

        self.dialog = ft.AlertDialog(
            shadow_color='red',
            modal=True,
            title=ft.Text("Update Available"),  # Ensure title is a `ft.Text` object
            content=ft.Container(
                width=300,
                height=150,
                content=update_content,
                alignment=ft.alignment.center,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.dialog)),
                ft.TextButton("Update", on_click=lambda e: self.start_update(url_item))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(self.dialog)
        self.page.update()

    class UpdateProgressDialog:
        def __init__(self, page):
            self.page = page
            self.dialog = None
            
            # Initialize UI components with consistent styling
            self.status_text = ft.Text(
                "Preparing download...",
                text_align=ft.TextAlign.CENTER,
                size=16,
                weight=ft.FontWeight.W_500
            )
            self.progress_bar = ft.ProgressBar(
                value=0,
                width=400,
                height=20,
                bar_height=8
            )

        def create(self):
            # Create dialog layout with responsive sizing
            self.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    "Downloading Update",
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.BOLD,
                    size=20
                ),
                content=self._create_content(),
                actions=[],
                actions_alignment=ft.MainAxisAlignment.CENTER
            )
            self.page.dialog = self.dialog  # Set the dialog
            self.dialog.open = True  # Open the dialog
            self.page.update()

        def _create_content(self):
            """Separate method for content creation to improve readability"""
            dialog_width = min(self.page.width * 0.8, 600)  # Cap max width
            dialog_height = min(self.page.height * 0.8, 300)  # Cap max height
            
            return ft.Container(
                width=dialog_width,
                height=dialog_height,
                content=ft.Column(
                    controls=[
                        self.status_text,
                        ft.Container(
                            content=self.progress_bar,
                            margin=ft.margin.symmetric(vertical=20),
                            alignment=ft.alignment.center
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                ),
                padding=20,
                alignment=ft.alignment.center
            )

        def update_progress(self, percentage, speed=None):
            """
            Update progress with speed display
            Args:
                percentage (float): Download progress percentage
                speed (str): Speed string (e.g., "1.5 MB/s")
            """
            speed_text = f" ({speed})" if speed else ""
            self.status_text.value = f"Downloading... {percentage:.1f}%{speed_text}"
            self.progress_bar.value = percentage / 100
            
            # Batch update all UI elements at once
            self.page.update()

        def close(self):
            """Close the dialog and clean up"""
            if self.dialog:
                self.dialog.open = False
                self.page.dialog = None
                self.dialog = None
                self.page.update()


    def start_update(self, url_item):
        """Start the update process synchronously."""
        asyncio.run(self.perform_update(url_item))


    async def perform_update(self, url_item):
        """Perform the update process asynchronously."""
        self.page.close(self.dialog)
        await asyncio.sleep(0.1)

        progress_dialog = self.UpdateProgressDialog(self.page)
        progress_dialog.create()

        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"update_installer_{os.getpid()}.exe")
        startup_script = os.path.join(temp_dir, f"run_update_{os.getpid()}.vbs")

        try:
            # Configure client for GitHub API
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers={
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'Python-App-Updater'
                }
            )

            # Get latest release info
            api_url = "https://api.github.com/repos/rizwan-hjp/tube-mp3-player/releases/latest"
            
            async with client as session:
                # Get release information
                release_response = await session.get(api_url)
                if release_response.status_code != 200:
                    raise Exception(f"Failed to get release info. Status: {release_response.status_code}")

                release_info = release_response.json()
                latest_version = release_info['tag_name'].lstrip('v').strip()
                print(f"Latest version from GitHub: {latest_version}")  # Debug print

                # Find Windows executable
                download_url = None
                for asset in release_info['assets']:
                    if asset['name'].endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break

                if not download_url:
                    raise ValueError("No Windows executable found in release")

                # Retry logic for download
                retries = 3
                for attempt in range(retries):
                    try:
                        async with session.stream('GET', download_url) as response:
                            if response.status_code != 200:
                                raise Exception(f"Failed to download update. HTTP status: {response.status_code}")

                            file_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            start_time = time.time()

                            if file_size == 0:
                                raise Exception("Content-Length is missing or zero.")

                            with open(temp_file, 'wb', buffering=8192*1024) as f:
                                chunk_size = 1024 * 1024  # 1MB chunk size
                                last_progress_update = 0

                                async for chunk in response.aiter_bytes(chunk_size):
                                    f.write(chunk)
                                    downloaded += len(chunk)

                                    # Update progress less frequently
                                    current_time = time.time()
                                    if current_time - last_progress_update >= 0.1:  # Update every 100ms
                                        progress = (downloaded / file_size) * 100
                                        elapsed = current_time - start_time
                                        speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                                        progress_dialog.update_progress(progress, f"{speed:.1f} MB/s")
                                        last_progress_update = current_time
                                        await asyncio.sleep(0.01)

                            # Ensure the full file was downloaded
                            if os.path.getsize(temp_file) != file_size:
                                raise Exception("Download incomplete. The file size doesn't match the expected size.")

                            # Wait for file to be fully written
                            await asyncio.sleep(1)

                            progress_dialog.close()

                            # Run the installer as admin
                            subprocess.Popen([temp_file])
                            await asyncio.sleep(1)

                            # Close the application
                            self.page.window_destroy()
                            break  # Exit the retry loop if the download succeeds

                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed: {e}")
                        if attempt == retries - 1:  # If this was the last retry, raise the exception
                            raise Exception(f"Update failed after {retries} attempts: {str(e)}")
                        await asyncio.sleep(2)  # Wait before retrying

        except Exception as e:
            if progress_dialog:
                progress_dialog.close()

            # Clean up incomplete download
            for file_path in [temp_file, startup_script]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as cleanup_error:
                        print(f"Error cleaning up file: {cleanup_error}")

            # Log the full exception traceback for better debugging
            print(f"Update failed: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())

    # Helper function to get version from string
    def get_version_tuple(version_str):
        """Convert version string to tuple for comparison."""
        return tuple(map(int, version_str.split('.')))


    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False    

    def run_as_admin(cmd):
        try:
            if UpdateButton.is_admin():
                return subprocess.run(
                    cmd, 
                    shell=False, 
                    capture_output=True, 
                    text=True
                )
            else:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", "cmd.exe", f"/c {cmd}", None, 1
                )
                return None
        except Exception:
            return None

    def show(self):
        """Initialize the update check process."""
        async def run_check():
            await self.check_for_updates()
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(run_check())
