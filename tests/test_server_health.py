import requests
import time
import sys

def check_health():
    url = "http://127.0.0.1:8001/"
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Server is up and running!")
                return True
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server... ({i+1}/{max_retries})")
            time.sleep(2)
    return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        print("Server failed to start.")
        sys.exit(1)
