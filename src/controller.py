import sys
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, QTimer, Qt
import src.config as config
import src.db as db
from src.ui.reminder_window import ReminderWindow
from src.ui.settings_window import SettingsWindow

class AppState:
    IDLE = "IDLE"
    WALKING_IN = "WALKING_IN"
    PROMPTING = "PROMPTING"
    SITTING_DOWN = "SITTING_DOWN"
    DRINKING = "DRINKING"
    HAPPY = "HAPPY"
    WALKING_OUT = "WALKING_OUT"
    SAD = "SAD"
    SLEEPING = "SLEEPING"
    SLEEPING_STIR = "SLEEPING_STIR"
    SLEEPING_WAKE = "SLEEPING_WAKE"

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
        self.window.drank_clicked.connect(self.on_drank_water)
        self.window.snooze_clicked.connect(self.on_snooze_clicked)
        
        # Initialize Database
        db.init_db()
        
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
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)
        
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

    def open_settings(self):
        """Opens the settings dialog."""
        print("Settings menu clicked!")
        self.settings_window = SettingsWindow(
            current_reminder_ms=self.reminder_interval_ms,
            current_snooze_ms=self.snooze_interval_ms,
            on_save_callback=self.set_intervals
        )
        self.settings_window.exec()

    def reset_reminder(self):
        """Resets the reminder timer."""
        self.start_reminder_timer()
        # If sleeping/snoozing, reset back to idle
        if self.state in [AppState.SLEEPING, AppState.SLEEPING_STIR, AppState.SLEEPING_WAKE, AppState.SAD]:
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
        """Cat finished walking in — play sit-down animation once, facing left."""
        self.state = AppState.SITTING_DOWN
        self.window.set_mirror(False)   # idle/sad sprites face left by default
        self.anim_manager.play("sad", loop=False)

    def on_drank_water(self):
        """State transitions when 'I Drank' is clicked."""
        self.state = AppState.HAPPY
        self.window.bubble.hide()
        
        # Record drink in DB
        db.record_drink()
        
        # Play happy celebration animation once (180ms per frame)
        self.anim_manager.play("happy", loop=False, interval_ms=180)

    def on_snooze_clicked(self):
        """State transitions when 'Snooze 5 Min' is clicked."""
        self.state = AppState.SAD
        self.window.bubble.hide()
        self.window.set_mirror(True)
        # Play sad animation (non-looping, slightly slower for effect)
        self.anim_manager.play("sad", loop=False, interval_ms=400)

    def on_animation_finished(self):
        """Handles state changes triggered by non-looping animation endings."""
        if self.state == AppState.SITTING_DOWN:
            # Sit down complete → show idle breathing/blinking animation + bubble
            self.state = AppState.PROMPTING
            self.window.set_mirror(True)
            self.anim_manager.play("idle", loop=True, interval_ms=10000)
            self._update_bubble_text()
            self.window.show_bubble()

        elif self.state == AppState.HAPPY:
            # Happy dance finished → walk cat back off-screen to the right
            self.state = AppState.WALKING_OUT
            self.window.start_walk_out(self.on_walk_out_complete)

        elif self.state == AppState.SAD:
            self.state = AppState.SLEEPING
            self.window.set_mirror(True)
            self.anim_manager.play("sleep", loop=False)
            # Snooze for the requested time minus 3 seconds for the stir sequence
            self.snooze_timer.start(max(0, self.snooze_interval_ms - 3000))

        elif self.state == AppState.SLEEPING_WAKE:
            # Wake animation finished → return to idle prompt
            self.state = AppState.PROMPTING
            self.window.set_mirror(True)
            self.anim_manager.play("idle", loop=True, interval_ms=10000)
            self.window.reset_button_states()
            self._update_bubble_text()
            self.window.show_bubble()

    def _update_bubble_text(self):
        """Updates the speech bubble with the current day's streak."""
        count = db.get_drinks_today()
        if count == 0:
            self.window.bubble.set_text("Time to drink some water!")
        elif count == 1:
            self.window.bubble.set_text("You've had 1 glass today! Another?")
        else:
            self.window.bubble.set_text(f"You've had {count} glasses today! Another?")

    def on_walk_out_complete(self):
        """Cat walked off screen — hide window and return to IDLE."""
        self.window.hide()
        self.anim_manager.stop()
        self.state = AppState.IDLE
        self.start_reminder_timer()

    def on_snooze_timeout(self):
        """Timer callback when snooze finishes."""
        if self.state == AppState.SLEEPING:
            self.state = AppState.SLEEPING_STIR
            self.anim_manager.play("sleep_stir", loop=True)
            self.snooze_timer.start(3000)
        elif self.state == AppState.SLEEPING_STIR:
            self.state = AppState.SLEEPING_WAKE
            self.snooze_timer.stop()
            self.anim_manager.play("sleep_wake", loop=False)

    def quit_app(self):
        """Gracefully shuts down the application."""
        self.reminder_timer.stop()
        self.snooze_timer.stop()
        self.window.close()
        self.tray_icon.hide()
        self.app.quit()
        sys.exit(0)
