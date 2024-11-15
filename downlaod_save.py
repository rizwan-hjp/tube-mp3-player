    

def update_progress(progress):
        progress_bar.value = progress / 100
        page.update()

def download_thread(url):
        try:
            progress_bar.visible = True
            status_text.value = "Getting video info..."
            page.update()

            info = youtube_downloader.get_video_info(url)
            video_title.value = info['original_title']
            page.update()

            status_text.value = "Downloading and converting..."
            page.update()

            file_path = youtube_downloader.download(url, update_progress)
            
            if os.path.exists(file_path):
                db.add_song(
                    info['original_title'],
                    file_path,
                    info['thumbnail'],
                    info['duration']
                )
                
                # refresh_playlist()
                status_text.value = "Ready to play!"
                play_button.disabled = False
                stop_button.disabled = False
            else:
                raise Exception(f"File not found: {file_path}")

        except Exception as e:
            status_text.value = f"Error: {str(e)}"
            play_button.disabled = True
            stop_button.disabled = True
        finally:
            progress_bar.visible = False
            url_input.disabled = False
            page.update()

    def start_download(e):
        if not url_input.value:
            status_text.value = "Please enter a YouTube URL"
            page.update()
            return

        url_input.disabled = True
        threading.Thread(target=download_thread, args=(url_input.value,), daemon=True).start()
