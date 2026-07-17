import sys
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, QTimer, Qt
import src.config as config
from src.ui.reminder_window import ReminderWindow

class AppState:
    IDLE = "IDLE"
    WALKING_IN = "WALKING_IN"
    PROMPTING = "PROMPTING"
    DRINKING = "DRINKING"
    HAPPY = "HAPPY"
    WALKING_OUT = "WALKING_OUT"
    SAD = "SAD"
    SLEEPING = "SLEEPING"
    WAKING = "WAKING"

class WaterCatController(QObject):
    """Main application controller coordinating state changes, timers, and background execution."""
    def __init__(self, anim_manager, app, parent=None):
        super().__init__(parent)
        self.anim_manager = anim_manager
        self.app = app
        self.state = AppState.IDLE
        
        # Core Timers
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.trigger_reminder)
        # Production default is 1 hour, can be adjusted in main via args
        self.reminder_interval_ms = config.DEFAULT_REMINDER_INTERVAL
        
        self.snooze_timer = QTimer(self)
        self.snooze_timer.timeout.connect(self.on_snooze_timeout)
        self.snooze_interval_ms = config.DEFAULT_SNOOZE_INTERVAL
        
        # Create UI
        self.window = ReminderWindow(self.anim_manager)
        
        # Connect UI Signals
        self.window.drank_clicked.connect(self.on_drank_clicked)
        self.window.snooze_clicked.connect(self.on_snooze_clicked)
        
        # Connect Animation Finished signal
        self.anim_manager.animation_finished.connect(self.on_animation_finished)
        
        # Setup tray icon
        self.setup_tray_icon()
        
        # Start background timer
        self.start_reminder_timer()
        print("WaterCat initialized silently in the background.")

    def set_intervals(self, reminder_ms, snooze_ms):
        """Allows command line overrides for testing (e.g. intervals in seconds)."""
        self.reminder_interval_ms = reminder_ms
        self.snooze_interval_ms = snooze_ms
        # Restart timer if running
        if self.reminder_timer.isActive():
            self.start_reminder_timer()

    def start_reminder_timer(self):
        """Starts/restarts the main reminder timer."""
        self.reminder_timer.stop()
        self.reminder_timer.start(self.reminder_interval_ms)
        print(f"Next water reminder in {self.reminder_interval_ms / 1000 / 60:.1f} minutes.")

    def setup_tray_icon(self):
        """Creates the system tray icon and context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create system tray icon from walk frame 0
        walk_frames = self.anim_manager.animations.get("walk", [])
        if walk_frames:
            # Use the first frame, scaled down nicely
            icon_pixmap = walk_frames[0].scaled(32, 32, Qt.KeepAspectRatio)
            self.tray_icon.setIcon(QIcon(icon_pixmap))
        else:
            # Fallback to standard style icon if assets are missing
            self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().SP_ComputerIcon))
            
        self.tray_icon.setToolTip("WaterCat - Hydration Companion")
        
        # Context Menu
        menu = QMenu()
        
        remind_action = QAction("Remind Now", self)
        remind_action.triggered.connect(self.force_reminder)
        menu.addAction(remind_action)
        
        reset_action = QAction("Reset Timer", self)
        reset_action.triggered.connect(self.reset_reminder)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def force_reminder(self):
        """Manually triggers a reminder immediately."""
        if self.state == AppState.IDLE:
            self.trigger_reminder()

    def reset_reminder(self):
        """Resets the reminder timer."""
        self.start_reminder_timer()
        # If sleeping/snoozing, reset back to idle
        if self.state in [AppState.SLEEPING, AppState.SAD, AppState.WAKING]:
            self.snooze_timer.stop()
            self.window.hide()
            self.anim_manager.stop()
            self.state = AppState.IDLE

    def trigger_reminder(self):
        """Transitions from IDLE to walking in and showing popup."""
        self.reminder_timer.stop()
        self.state = AppState.WALKING_IN
        self.window.reset_button_states()
        self.window.start_walk_in(self.on_walk_in_complete)

    def on_walk_in_complete(self):
        """Cat finished walking in, show the speech bubble and await input."""
        self.state = AppState.PROMPTING
        # Stop walk loop and play standing idle pose (happy/wake frame or walk frame 0 static)
        # Using a quiet standing state
        self.anim_manager.play("walk", loop=False) # Plays once and stops on frame 7 or 0
        self.window.show_bubble()

    def on_drank_clicked(self):
        """State transitions when 'I Drank Water' is clicked."""
        self.state = AppState.HAPPY
        self.window.bubble.hide()
        # Play happy celebration animation immediately slowly (180ms per frame)
        self.anim_manager.play("happy", loop=False, interval_ms=180)

    def on_snooze_clicked(self):
        """State transitions when 'Snooze 5 Min' is clicked."""
        self.state = AppState.SAD
        self.window.bubble.hide()
        # Play sad animation (non-looping)
        self.anim_manager.play("sad", loop=False)

    def on_animation_finished(self):
        """Handles state changes triggered by non-looping animation endings."""
        if self.state == AppState.HAPPY:
            self.state = AppState.WALKING_OUT
            # Walk out of screen, then hide
            self.window.start_walk_out(self.on_walk_out_complete)
            
        elif self.state == AppState.SAD:
            self.state = AppState.SLEEPING
            # Sleep looping animation
            self.anim_manager.play("sleep", loop=True)
            # Start the snooze timer
            self.snooze_timer.start(self.snooze_interval_ms)
            print(f"Snoozing for {self.snooze_interval_ms / 1000 / 60:.1f} minutes.")
            
        elif self.state == AppState.WAKING:
            # Woken up, prompt again
            self.state = AppState.PROMPTING
            self.window.reset_button_states()
            self.window.show_bubble()

    def on_walk_out_complete(self):
        """Cat walked off screen, close window and return to IDLE."""
        self.window.hide()
        self.anim_manager.stop()
        self.state = AppState.IDLE
        self.start_reminder_timer()

    def on_snooze_timeout(self):
        """Timer callback when snooze finishes."""
        self.snooze_timer.stop()
        self.state = AppState.WAKING
        # Play wake up animation
        self.anim_manager.play("wake", loop=False)

    def quit_app(self):
        """Gracefully shuts down the application."""
        self.reminder_timer.stop()
        self.snooze_timer.stop()
        self.window.close()
        self.tray_icon.hide()
        self.app.quit()
        sys.exit(0)
