import os
import sys

import json

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Ensure assets dir exists
os.makedirs(ASSETS_DIR, exist_ok=True)

# Configuration Options
DEFAULT_REMINDER_INTERVAL = 60 * 60 * 1000  # 1 hour in milliseconds
DEFAULT_SNOOZE_INTERVAL = 5 * 60 * 1000     # 5 minutes in milliseconds

# Load user settings if they exist
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r") as f:
            user_settings = json.load(f)
            if "reminder_interval_ms" in user_settings:
                DEFAULT_REMINDER_INTERVAL = user_settings["reminder_interval_ms"]
            if "snooze_interval_ms" in user_settings:
                DEFAULT_SNOOZE_INTERVAL = user_settings["snooze_interval_ms"]
    except Exception as e:
        print(f"Failed to load settings.json: {e}")

# Animation settings
FRAME_RATE_FPS = 5                          # 5 frames per second for natural speed
FRAME_DURATION_MS = 1000 // FRAME_RATE_FPS  # 200ms per frame
SPRITE_SCALE = 1                            # 1x native unscaled pixel-art resolution

# Standard uniform dimensions for all cat sprites in the application
TARGET_WIDTH = 128
TARGET_HEIGHT = 123

# Folder names for individual frame images
SPRITE_CONFIGS = {
    "walk": {"folder": "walk"},
    "idle": {"folder": "idle", "frame_indices": [0, 1]},
    "happy": {"folder": "happy_dance"},
    "sad": {"folder": "sit_down", "frame_indices": [0, 2, 4, 6]},
    "sleep": {"folder": "sleep_loop", "frame_indices": [0, 1, 2, 3]},
    "sleep_stir": {"folder": "sleep_loop", "frame_indices": [3, 4]},
    "sleep_wake": {"folder": "sleep_loop", "frame_indices": [4, 5, 6, 7, 0]}
}

# Typography
FONT_FILENAME = "PressStart2P-Regular.ttf"
FONT_PATH = os.path.join(ASSETS_DIR, FONT_FILENAME)

# UI Theme (Retro Pixel Colors)
COLOR_BG_LIGHT = "#FFFFFF"
COLOR_BG_DARK = "#2D2D2D"
COLOR_TEXT = "#000000"
COLOR_TEXT_MUTED = "#555555"
COLOR_BORDER = "#000000"
COLOR_BUBBLE_BG = "#FFFFFF"

# Retro Button Colors
COLOR_BTN_PRIMARY_BG = "#4C9EEB"      # Blue button
COLOR_BTN_PRIMARY_BORDER = "#1F5F99"
COLOR_BTN_PRIMARY_TEXT = "#FFFFFF"

# Reset / snooze buttons
COLOR_BTN_SECONDARY_BG = "#E5E5E5"    # Gray button
COLOR_BTN_SECONDARY_BORDER = "#999999"
COLOR_BTN_SECONDARY_TEXT = "#000000"

# Sound (If needed later, easy to add)
SOUND_ENABLED = False
