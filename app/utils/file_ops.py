import os
import shutil
import requests
import logging

logger = logging.getLogger(__name__)

def download_file(url, local_filename):
    """Downloads a file from a URL to a local path."""
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with requests.get(url, stream=True, timeout=30, headers=headers) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {str(e)}", exc_info=True)
        return False

def cleanup_temp_dir(directory):
    """Deletes the temporary directory with retry on Windows."""
    if not os.path.exists(directory):
        return
    
    for attempt in range(5):
        try:
            shutil.rmtree(directory)
            return
        except PermissionError:
            import time
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
            return
