from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt
import src.config as config

class AnimatedSprite(QWidget):
    """Widget responsible for rendering a single frame of the character animation.
    
    Contains frame reference updates and horizontal mirroring, ensuring only a
    single sliced frame of the sprite sheet is drawn to the screen at any time.
    """
    def __init__(self, anim_manager, parent=None):
        super().__init__(parent)
        self.anim_manager = anim_manager
        self.mirror_horizontal = False
        
        # Connect animation frame changes to trigger paint updates
        self.anim_manager.frame_changed.connect(self.on_frame_changed)
        
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(config.TARGET_WIDTH, config.TARGET_HEIGHT)

    def on_frame_changed(self, pixmap):
        """Callback when the animation frame index changes."""
        self.update()

    def paintEvent(self, event):
        """Renders exactly one sliced frame of the active animation."""
        painter = QPainter(self)
        # Ensure crisp, non-blurred rendering for retro pixel-art sprites
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        
        pixmap = self.anim_manager.get_current_frame()
        if not pixmap.isNull():
            w = int(pixmap.width() * config.SPRITE_SCALE)
            h = int(pixmap.height() * config.SPRITE_SCALE)
            
            # Position character centered and aligned to bottom baseline inside widget canvas
            x = (self.width() - w) // 2
            y = self.height() - h
            
            if self.mirror_horizontal:
                painter.save()
                # Translate to right edge of draw region and scale -1 horizontally to flip
                painter.translate(x + w, y)
                painter.scale(-1, 1)
                painter.drawPixmap(0, 0, w, h, pixmap)
                painter.restore()
            else:
                painter.drawPixmap(x, y, w, h, pixmap)
