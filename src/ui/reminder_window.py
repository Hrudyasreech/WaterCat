from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QPainter, QColor
import src.config as config
from src.ui.bubble import PixelBubble
from src.ui.button import PixelButton
from src.ui.cat_widget import CatWidget

class ReminderWindow(QWidget):
    """Frameless, transparent desktop popup displaying the companion and buttons."""
    # Signals to communicate button clicks back to the main controller
    drank_clicked = Signal()
    snooze_clicked = Signal()

    def __init__(self, anim_manager, parent=None):
        super().__init__(parent)
        self.anim_manager = anim_manager
        
        # Windows-specific frameless, stay-on-top, and taskbar-less flags
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Window size - scaled down to native size
        self.window_width = 240
        self.window_height = 220
        self.resize(self.window_width, self.window_height)
        
        # Position at bottom-right corner of screen
        self.reposition_to_bottom_right()
        
        # Cat walking parameters - starts off-screen right
        self.cat_x = self.window_width
        self.walk_target_x = 56         # Resting X position (centered: (240 - 128) // 2)
        self.walk_direction = -1        # -1 = walking left (in), 1 = walking right (out)
        self.is_walking = False
        self.on_walk_complete = None
        
        self.setup_ui()

    def setup_ui(self):
        # 1. Create Speech Bubble (manual geometry positioning)
        self.bubble = PixelBubble("Time to drink some water!", self)
        # Custom size: 220px wide, 110px tall, placed with padding
        self.bubble.setGeometry(10, 10, 220, 110)
        
        # Add buttons inside bubble's layout (below the text)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        button_layout.setContentsMargins(0, 4, 0, 0)
        
        # Shortened button text to fit nicely in 220px bubble
        self.btn_drank = PixelButton("I Drank", is_primary=True)
        self.btn_snooze = PixelButton("Snooze", is_primary=False)
        
        button_layout.addWidget(self.btn_drank)
        button_layout.addWidget(self.btn_snooze)
        
        # Add layout to bubble
        self.bubble.layout().addLayout(button_layout)
        
        # Connect buttons
        self.btn_drank.clicked.connect(self.on_drank_water)
        self.btn_snooze.clicked.connect(self.on_snooze)
        
        # 2. Create Cat Widget (direct child, manual geometry)
        self.cat_widget = CatWidget(self.anim_manager, self)
        
        # Connect frame changes to coordinate both sprite rendering and walking movement
        self.anim_manager.frame_changed.connect(self.on_cat_frame_changed)
        
        # Make sure bubble is initially hidden (cat walks in first)
        self.bubble.hide()

    def on_cat_frame_changed(self, pixmap):
        """Callback triggered when the animation frame changes.
        
        Synchronizes the cat's coordinate updates directly with the animation ticks
        and dynamically sets the mirroring flag.
        """
        if pixmap.isNull():
            return
            
        anim_name = self.anim_manager.current_animation
        h = int(pixmap.height() * config.SPRITE_SCALE)
        y = self.window_height - h
        
        # Determine mirroring based on walk direction and animation name
        if self.is_walking:
            if self.walk_direction == -1:
                # Walking left (in) -> Mirror to face right (moonwalk in)
                self.cat_widget.mirror_horizontal = True
            else:
                # Walking right (out) -> No mirror to face left (moonwalk out)
                self.cat_widget.mirror_horizontal = False
        else:
            # Idle/Acting states: Always face LEFT (towards the speech bubble/buttons)
            if anim_name in ["walk", "sleep"]:
                # Default direction in JPEG is left -> No mirror
                self.cat_widget.mirror_horizontal = False
            elif anim_name in ["happy", "sad", "wake"]:
                # Default direction in JPEG is right -> Mirror to face left
                self.cat_widget.mirror_horizontal = True
                
        # Walk coordinate update
        if self.is_walking:
            step = 8  
            self.cat_x += self.walk_direction * step
            
            # Check if target reached
            reached = False
            if self.walk_direction == -1 and self.cat_x <= self.walk_target_x:
                self.cat_x = self.walk_target_x
                reached = True
            elif self.walk_direction == 1 and self.cat_x >= self.walk_target_x:
                self.cat_x = self.walk_target_x
                reached = True
                
            if reached:
                self.is_walking = False
                if self.on_walk_complete:
                    cb = self.on_walk_complete
                    self.on_walk_complete = None
                    # Defer callback to next event loop cycle
                    QTimer.singleShot(0, cb)
                    
        self.cat_widget.move(self.cat_x, y)

    def paintEvent(self, event):
        """Clears the background to transparent. Required for proper Windows desktop alpha blending."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def reposition_to_bottom_right(self):
        """Moves the window near the bottom-right corner of the primary screen."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            # 15px margin from screen edges
            x = rect.x() + rect.width() - self.window_width - 15
            y = rect.y() + rect.height() - self.window_height - 15
            self.move(x, y)

    def start_walk_in(self, callback):
        """Starts the walk-in animation from the right of the window (moving left, facing right)."""
        self.reposition_to_bottom_right()
        self.bubble.hide()
        
        # Position cat off-screen right
        self.cat_x = self.window_width
        
        # Initial Y position alignment
        h = self.cat_widget.height()
        self.cat_widget.move(self.cat_x, self.window_height - h)
        self.show()
        
        # Set up walk-in parameters
        self.is_walking = True
        self.walk_direction = -1
        self.walk_target_x = (self.window_width - self.cat_widget.width()) // 2
        self.on_walk_complete = callback
        
        # Start walk animation
        self.anim_manager.play("walk", loop=True)

    def start_walk_out(self, callback):
        """Starts the walk-out animation to the right of the window (moving right, facing right)."""
        self.bubble.hide()
        
        self.is_walking = True
        self.walk_direction = 1
        self.walk_target_x = self.window_width
        self.on_walk_complete = callback
        
        # Start walk animation
        self.anim_manager.play("walk", loop=True)

    def show_bubble(self):
        """Displays the text speech bubble once the cat is in position."""
        self.bubble.show()

    def on_drank_water(self):
        """Handles I Drank Water button click."""
        self.btn_drank.setEnabled(False)
        self.btn_snooze.setEnabled(False)
        self.drank_clicked.emit()

    def on_snooze(self):
        """Handles Snooze button click."""
        self.btn_drank.setEnabled(False)
        self.btn_snooze.setEnabled(False)
        self.snooze_clicked.emit()

    def reset_button_states(self):
        """Re-enables buttons for the next prompt."""
        self.btn_drank.setEnabled(True)
        self.btn_snooze.setEnabled(True)
