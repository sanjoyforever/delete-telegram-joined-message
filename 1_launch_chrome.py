"""
Script 1: Launch Chrome with remote debugging on port 9222 and open Telegram Web.
Run this first, log in with your phone, then run script 2.
"""

import subprocess
import sys
import os

# Common Chrome executable paths on Windows
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

# Use a dedicated profile dir so your main Chrome profile is untouched
PROFILE_DIR = os.path.join(os.path.dirname(__file__), "chrome_profile")

def find_chrome():
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    return None

def main():
    chrome = find_chrome()
    if not chrome:
        print("ERROR: Chrome not found. Set the path manually in this script.")
        sys.exit(1)

    os.makedirs(PROFILE_DIR, exist_ok=True)

    cmd = [
        chrome,
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://web.telegram.org/k/",
    ]

    print(f"Launching Chrome with remote debugging on port 9222...")
    print(f"Profile dir: {PROFILE_DIR}")
    print("Open Telegram, log in with your phone, then run script 2.")
    subprocess.Popen(cmd)

if __name__ == "__main__":
    main()
