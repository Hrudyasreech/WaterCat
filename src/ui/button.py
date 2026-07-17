from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont
import src.config as config

class PixelButton(QPushButton):
    """Custom QPushButton styled with a retro pixel-art aesthetic."""
    def __init__(self, text, is_primary=True, parent=None):
        super().__init__(text, parent)
        self.is_primary = is_primary
        self.setup_ui()

    def setup_ui(self):
        # Set pixel font
        font = QFont("Press Start 2P")
        # Pixel fonts render best at specific sizes (typically multiples of 8px/9px)
        font.setPixelSize(8)
        self.setFont(font)
        
        # Retro styling
        if self.is_primary:
            bg_color = config.COLOR_BTN_PRIMARY_BG
            border_color = config.COLOR_BTN_PRIMARY_BORDER
            text_color = config.COLOR_BTN_PRIMARY_TEXT
            hover_bg = "#6CAFEF"
            pressed_bg = "#1F5F99"
        else:
            bg_color = config.COLOR_BTN_SECONDARY_BG
            border_color = config.COLOR_BTN_SECONDARY_BORDER
            text_color = config.COLOR_BTN_SECONDARY_TEXT
            hover_bg = "#F2F2F2"
            pressed_bg = "#B5B5B5"
            
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid {config.COLOR_BORDER};
                border-bottom-width: 4px; /* Thicker bottom border for retro bevel look */
                color: {text_color};
                padding: 4px 8px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
                border-top-width: 4px;     /* Offsets the height when pressed */
                border-bottom-width: 2px;  /* Creates retro pressed-down effect */
                padding-top: 6px;
                padding-bottom: 2px;
            }}
        """
        self.setStyleSheet(style)
        # Prevent focus rectangle which ruins pixel look
        self.setFocusPolicy(self.focusPolicy().NoFocus)
