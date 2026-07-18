from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QPainter
import src.config as config
from src.ui.bubble import PixelBubble
from src.ui.button import PixelButton
from src.ui.animated_sprite import AnimatedSprite


class ReminderWindow(QWidget):
    """Full-screen-width transparent overlay that hosts the cat sprite and speech bubble.

    Architecture:
    - The window spans the FULL width of the screen and sits at the bottom edge.
      Height is just enough to show the cat + bubble above it.
    - The AnimatedSprite widget is a child positioned at (cat_x, cat_y) in screen-local
      coordinates, where cat_x goes from off-screen right to the resting position.
    - The speech bubble floats just above the sprite at the same x.
    - A high-precision 60 FPS movement timer controls cat_x via velocity.
    - A separate animation timer (inside AnimationManager) only advances frame indices.
      These two timers are completely independent.
    """
    drank_clicked = Signal()
    snooze_clicked = Signal()

    # Sprite resting position: distance from right edge of screen to the cat center
    REST_RIGHT_MARGIN = 130    # px from right edge of screen where cat sits

    # Movement speed: pixels per 60 FPS tick
    WALK_SPEED = 1.0           # ~60 px/sec

    def __init__(self, anim_manager, parent=None):
        super().__init__(parent)
        self.anim_manager = anim_manager

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Get screen dimensions
        screen = QGuiApplication.primaryScreen()
        rect = screen.availableGeometry() if screen else None
        self.screen_x      = rect.x()      if rect else 0
        self.screen_y      = rect.y()      if rect else 0
        self.screen_w      = rect.width()  if rect else 1920
        self.screen_h      = rect.height() if rect else 1080

        # Window spans full screen width; tall enough for bubble + cat
        self.win_h = config.TARGET_HEIGHT + 130   # 130px for bubble above cat
        self.setGeometry(
            self.screen_x,
            self.screen_y + self.screen_h - self.win_h,
            self.screen_w,
            self.win_h
        )

        # Cat screen-local X coordinate (relative to this window's left edge)
        # Starts fully off-screen to the right
        self.cat_x = float(self.screen_w + config.TARGET_WIDTH)
        # Y of sprite: bottom of window minus sprite height
        self.cat_y = self.win_h - config.TARGET_HEIGHT

        # Walk target: cat stops at this local x
        self.rest_x = float(self.screen_w - self.REST_RIGHT_MARGIN - config.TARGET_WIDTH // 2)
        # Off-screen right exit x
        self.exit_x = float(self.screen_w + config.TARGET_WIDTH)

        # Walking state
        self.is_walking    = False
        self.walk_velocity = 0.0      # positive = right, negative = left
        self.walk_target_x = 0.0
        self._walk_done_cb = None

        # High-precision movement timer (60 FPS, independent of animation timer)
        self._move_timer = QTimer(self)
        self._move_timer.setTimerType(Qt.PreciseTimer)
        self._move_timer.setInterval(16)          # ~62.5 FPS
        self._move_timer.timeout.connect(self._on_move_tick)

        # Horizontal mirror state
        self._mirror = False

        self._build_ui()

        # Listen to frame changes only to update mirror flag (NOT to move the widget)
        self.anim_manager.frame_changed.connect(self._on_frame_changed)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Speech bubble (hidden until cat arrives)
        self.bubble = PixelBubble("Time to drink some water!", self)
        self.bubble.setFixedSize(220, 110)
        self.bubble.hide()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 4, 0, 0)
        self.btn_drank  = PixelButton("I Drank",  is_primary=True)
        self.btn_snooze = PixelButton("Snooze",   is_primary=False)
        btn_row.addWidget(self.btn_drank)
        btn_row.addWidget(self.btn_snooze)
        self.bubble.layout().addLayout(btn_row)

        self.btn_drank.clicked.connect(self.on_drank_water)
        self.btn_snooze.clicked.connect(self.on_snooze)

        # Animated sprite widget
        self.sprite = AnimatedSprite(self.anim_manager, self)
        self.sprite.resize(config.TARGET_WIDTH, config.TARGET_HEIGHT)
        self.sprite.move(int(self.cat_x), self.cat_y)

    # ------------------------------------------------------------------
    # Frame-change callback — updates mirror only, does NOT move
    # ------------------------------------------------------------------
    def _on_frame_changed(self, pixmap):
        self.sprite.mirror_horizontal = self._mirror
        self.sprite.update()

    # ------------------------------------------------------------------
    # 60 FPS movement tick — updates cat_x via velocity, then moves sprite
    # ------------------------------------------------------------------
    def _on_move_tick(self):
        self.cat_x += self.walk_velocity

        # Check destination
        reached = (
            (self.walk_velocity < 0 and self.cat_x <= self.walk_target_x) or
            (self.walk_velocity > 0 and self.cat_x >= self.walk_target_x)
        )
        if reached:
            self.cat_x = self.walk_target_x
            self.is_walking = False
            self._move_timer.stop()
            self.sprite.move(int(self.cat_x), self.cat_y)
            if self._walk_done_cb:
                cb, self._walk_done_cb = self._walk_done_cb, None
                QTimer.singleShot(0, cb)
            return

        self.sprite.move(int(self.cat_x), self.cat_y)

    # ------------------------------------------------------------------
    # Public walk API
    # ------------------------------------------------------------------
    def start_walk_in(self, callback):
        """Walk cat in from the right edge to the resting position."""
        self.cat_x         = self.exit_x
        self.walk_target_x = self.rest_x
        self.walk_velocity = -self.WALK_SPEED   # moving left
        self._walk_done_cb = callback
        self._mirror       = True               # walk.png faces right → mirror to face left

        self.is_walking = True
        self.anim_manager.play("walk", loop=True)
        self.sprite.move(int(self.cat_x), self.cat_y)
        self._position_bubble()
        self.bubble.hide()
        self.show()
        self._move_timer.start()

    def start_walk_out(self, callback):
        """Walk cat out to the right edge from its current resting position."""
        self.walk_target_x = self.exit_x
        self.walk_velocity = +self.WALK_SPEED   # moving right
        self._walk_done_cb = callback
        self._mirror       = False              # walk.png faces right → no mirror when walking right

        self.is_walking = True
        self.anim_manager.play("walk", loop=True)
        self.bubble.hide()
        self._move_timer.start()

    # ------------------------------------------------------------------
    # Bubble positioning
    # ------------------------------------------------------------------
    def _position_bubble(self):
        """Place bubble centred above the resting cat position."""
        bw = self.bubble.width()
        bx = int(self.rest_x + config.TARGET_WIDTH // 2 - bw // 2)
        by = self.cat_y - self.bubble.height() - 4
        bx = max(4, min(bx, self.screen_w - bw - 4))
        self.bubble.move(bx, by)

    def show_bubble(self):
        self._position_bubble()
        self.bubble.show()

    # ------------------------------------------------------------------
    # Static state helpers
    # ------------------------------------------------------------------
    def set_mirror(self, mirror: bool):
        self._mirror = mirror
        self.sprite.mirror_horizontal = mirror
        self.sprite.update()

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------
    def on_drank_water(self):
        self.btn_drank.setEnabled(False)
        self.btn_snooze.setEnabled(False)
        self.drank_clicked.emit()

    def on_snooze(self):
        self.btn_drank.setEnabled(False)
        self.btn_snooze.setEnabled(False)
        self.snooze_clicked.emit()

    def reset_button_states(self):
        self.btn_drank.setEnabled(True)
        self.btn_snooze.setEnabled(True)
