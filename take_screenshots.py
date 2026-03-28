"""
SelfCore — Desktop Screenshot Utility
Takes a full desktop screenshot for marketing purposes.
"""
import time
import os

try:
    import requests
except ImportError:
    requests = None

try:
    import pyautogui
    from PIL import Image
except ImportError:
    print("ERROR: pyautogui and Pillow required. pip install pyautogui Pillow")
    exit(1)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marketing")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Wait for Next.js to be ready
if requests:
    print("Waiting for Next.js on localhost:3000...")
    for i in range(30):
        try:
            r = requests.get("http://localhost:3000", timeout=1)
            if r.status_code == 200:
                print(f"Next.js ready after {i+1}s")
                break
        except Exception:
            time.sleep(1)
    else:
        print("WARNING: Next.js not responding, taking screenshot anyway")

# Take full desktop screenshot
time.sleep(2)
screenshot = pyautogui.screenshot()
screenshot.save(os.path.join(OUTPUT_DIR, "desktop_full.png"))
print(f"Desktop screenshot saved to {OUTPUT_DIR}/desktop_full.png")
print(f"Size: {screenshot.size[0]}x{screenshot.size[1]}")
