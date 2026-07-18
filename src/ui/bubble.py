from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, QPoint
import src.config as config

class PixelBubble(QWidget):
    """Custom speech bubble widget with a retro pixelated appearance."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.tail_height = 12
        self.tail_width = 16
        # The tail will point down and to the left (where the cat stands)
        self.tail_offset_x = 40 
        self.setup_ui()

    def set_text(self, text):
        self.text = text
        # Use HTML rich text to force line spacing since pixel fonts often have broken metrics
        self.label.setText(f"<div style='line-height:1.5;'>{self.text}</div>")

    def setup_ui(self):
        # We need a layout to contain the text label
        layout = QVBoxLayout(self)
        # Add padding so the text fits inside the bubble frame
        layout.setContentsMargins(10, 10, 10, 10 + self.tail_height)
        
        self.label = QLabel(self.text, self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        
        # Load pixel font
        font = QFont("Press Start 2P")
        font.setPixelSize(10)
        self.label.setFont(font)
        
        # Style label text (Qt does not support CSS line-height on plain text QLabel)
        self.label.setStyleSheet(f"color: {config.COLOR_TEXT};")
        layout.addWidget(self.label)

    def paintEvent(self, event):
        painter = QPainter(self)
        # CRITICAL: Disable antialiasing for sharp pixel-art edges
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        w = self.width()
        h = self.height()
        
        # Bubble body boundaries
        rect_w = w - 4
        rect_h = h - self.tail_height - 4
        
        # Coordinates
        x0, y0 = 2, 2
        x1, y1 = rect_w, rect_h
        
        # Setup pen and brush
        pen = QPen(QColor(config.COLOR_BORDER), 2, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        brush = QBrush(QColor(config.COLOR_BUBBLE_BG), Qt.SolidPattern)
        
        painter.setPen(pen)
        painter.setBrush(brush)
        
        # Create blocky rounded rectangle path
        # We draw a polygon with truncated (pixel-stair) corners
        # Offset 4px for blocky corner truncation
        corner = 4
        
        bubble_polygon = QPolygon([
            # Top edge
            QPoint(x0 + corner, y0),
            QPoint(x1 - corner, y0),
            QPoint(x1, y0 + corner),
            
            # Right edge
            QPoint(x1, y1 - corner),
            QPoint(x1 - corner, y1),
            
            # Bottom edge (right of tail)
            QPoint(self.tail_offset_x + self.tail_width, y1),
            # Tail tip (pointing down-left)
            QPoint(self.tail_offset_x, y1 + self.tail_height),
            QPoint(self.tail_offset_x + self.tail_width // 2, y1),
            
            QPoint(x0 + corner, y1),
            QPoint(x0, y1 - corner),
            
            # Left edge
            QPoint(x0, y0 + corner)
        ])
        
        # Draw the bubble body and tail together
        painter.drawPolygon(bubble_polygon)
        
        # Overwrite the border line inside the tail connection to make it hollow
        # We draw a white line over the connection segment
        painter.setPen(QPen(QColor(config.COLOR_BUBBLE_BG), 2))
        painter.drawLine(
            self.tail_offset_x + 2, y1,
            self.tail_offset_x + self.tail_width - 2, y1
        )
