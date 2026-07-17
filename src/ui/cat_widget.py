from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt
import src.config as config

class CatWidget(QWidget):
    """Widget responsible for rendering the cat sprite with crisp pixel-art scaling."""
    def __init__(self, anim_manager, parent=None):
        super().__init__(parent)
        self.anim_manager = anim_manager
        self.mirror_horizontal = False  # Set to True to flip sprite (e.g. walking right)
        
        # Connect animation frames to update the widget
        self.anim_manager.frame_changed.connect(self.on_frame_changed)
        
        # Transparent background for the widget itself
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Default size based on standing frame size * scale
        cfg = config.SPRITE_CONFIGS["walk"]
        self.setMinimumSize(
            int(cfg["base_width"] * config.SPRITE_SCALE),
            int(cfg["base_height"] * config.SPRITE_SCALE)
        )

    def on_frame_changed(self, pixmap):
        """Callback when the animation frame changes."""
        if not pixmap.isNull():
            w = int(pixmap.width() * config.SPRITE_SCALE)
            h = int(pixmap.height() * config.SPRITE_SCALE)
            self.setMinimumSize(w, h)
            self.resize(w, h)
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # CRITICAL: Ensure nearest-neighbor scaling (never blur pixel art)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        
        pixmap = self.anim_manager.get_current_frame()
        if not pixmap.isNull():
            w = int(pixmap.width() * config.SPRITE_SCALE)
            h = int(pixmap.height() * config.SPRITE_SCALE)
            
            # Align to bottom and horizontal center
            x = (self.width() - w) // 2
            y = self.height() - h
            
            if self.mirror_horizontal:
                painter.save()
                # Translate to the right side of target region, scale -1 on X axis
                painter.translate(x + w, y)
                painter.scale(-1, 1)
                painter.drawPixmap(0, 0, w, h, pixmap)
                painter.restore()
            else:
                painter.drawPixmap(x, y, w, h, pixmap)
