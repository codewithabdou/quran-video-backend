import requests
import json
import sys

def verify_live_generation():
    url = "http://127.0.0.1:8000/api/v1/generate-video"
    payload = {
        "surah": 108,
        "ayah_start": 1,
        "ayah_end": 1,
        "platform": "reel"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=120) # High timeout for video generation
        
        if response.status_code == 200:
            print("Success! Status code 200.")
            if response.headers.get("content-type") == "video/mp4":
                print("Content-Type is video/mp4.")
                output_file = "live_generated_video.mp4"
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"Video saved to {output_file}")
                # Check file size
                import os
                size = os.path.getsize(output_file)
                print(f"File size: {size} bytes")
                if size > 1000:
                    print("Verification PASSED.")
                else:
                    print("Verification FAILED: File too small.")
            else:
                print(f"Verification FAILED: Content-Type is {response.headers.get('content-type')}")
        else:
            print(f"Verification FAILED: Status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Verification FAILED: Exception {e}")

if __name__ == "__main__":
    verify_live_generation()
