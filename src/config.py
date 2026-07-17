import os
import sys

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ensure assets dir exists
os.makedirs(ASSETS_DIR, exist_ok=True)

# Configuration Options
DEFAULT_REMINDER_INTERVAL = 60 * 60 * 1000  # 1 hour in milliseconds
DEFAULT_SNOOZE_INTERVAL = 5 * 60 * 1000     # 5 minutes in milliseconds

# Animation settings
FRAME_RATE_FPS = 10                         # 10 frames per second
FRAME_DURATION_MS = 1000 // FRAME_RATE_FPS  # 100ms per frame
SPRITE_SCALE = 1                            # 1x native unscaled pixel-art resolution

# Standard uniform dimensions for all cat sprites in the application
TARGET_WIDTH = 128
TARGET_HEIGHT = 123

# Raw sprite sheet configs (used for correct horizontal slicing)
SPRITE_CONFIGS = {
    "walk": {"filename": "walk.jpg", "frames": 8, "base_width": 128, "base_height": 123, "bg_threshold": 200},
    "happy": {"filename": "happy2.jpg", "frames": 8, "base_width": 128, "base_height": 159, "crop_y": (196, 355), "bg_threshold": 175},
    "sad": {"filename": "sad.jpg", "frames": 6, "base_width": 170.67, "base_height": 167, "bg_threshold": 200},
    "sleep": {"filename": "sleep.jpg", "frames": 6, "base_width": 170.67, "base_height": 168, "bg_threshold": 200},
    "wake": {"filename": "wake.jpg", "frames": 8, "base_width": 128, "base_height": 123, "bg_threshold": 200}
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
