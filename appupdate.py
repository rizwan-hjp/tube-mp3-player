import requests

async def get_latest_release():
    """Fetch the latest release version and download URL from GitHub API."""
    api_url = "https://api.github.com/repos/rizwan-hjp/tube-mp3-player/releases/latest"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Python-App-Updater'
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        release_info = response.json()
        
        # Remove 'v' prefix if present and clean the version string
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

        return {latest_version,download_url}
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching release info: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing release info: {e}")
        return None
