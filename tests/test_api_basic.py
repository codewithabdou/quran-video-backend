import requests
import time
import sys
import unittest

class TestVideoGenerator(unittest.TestCase):
    BASE_URL = "http://127.0.0.1:8000"

    def test_root(self):
        resp = requests.get(f"{self.BASE_URL}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome", resp.json()["message"])

    def test_health(self):
        # Allow server some time to start up if running in batch
        pass

if __name__ == "__main__":
    # Simple wait for server
    print("Waiting for server to be ready...")
    for _ in range(5):
        try:
            requests.get("http://127.0.0.1:8000/")
            break
        except:
            time.sleep(1)
            
    unittest.main()
