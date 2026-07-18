import json
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QMessageBox, QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QMouseEvent
import src.config as config
from src.ui.button import PixelButton

class SettingsWindow(QDialog):
    """A settings dialog for the WaterCat application, styled as a complete frameless retro pixel-art box."""
    
    def __init__(self, parent=None, current_reminder_ms=None, current_snooze_ms=None, on_save_callback=None):
        super().__init__(parent)
        
        # Make the window frameless so we can draw a custom retro border
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(320, 200)
        
        self.on_save_callback = on_save_callback
        self.drag_pos = None
        
        # Convert ms to minutes for user display
        rem_min = (current_reminder_ms or config.DEFAULT_REMINDER_INTERVAL) // 60000
        snooze_min = (current_snooze_ms or config.DEFAULT_SNOOZE_INTERVAL) // 60000
        
        self.setup_ui(rem_min, snooze_min)
        
    def setup_ui(self, rem_min, snooze_min):
        retro_font = QFont("Press Start 2P")
        retro_font.setPixelSize(11)
        self.setFont(retro_font)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # The inner styled widget
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QWidget#container {{
                background-color: {config.COLOR_BG_LIGHT};
                border: 4px solid {config.COLOR_BORDER};
            }}
            QLabel {{
                color: {config.COLOR_TEXT};
            }}
            QSpinBox {{
                background-color: {config.COLOR_BG_LIGHT};
                border: 2px solid {config.COLOR_BORDER};
                color: {config.COLOR_TEXT};
                padding: 2px;
                selection-background-color: {config.COLOR_BTN_PRIMARY_BG};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {config.COLOR_BTN_SECONDARY_BG};
                border: 1px solid {config.COLOR_BORDER};
                width: 16px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {config.COLOR_BTN_PRIMARY_BG};
            }}
        """)
        
        # Container Layout
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 10, 15, 15)
        
        # --- Custom Title Bar ---
        title_layout = QHBoxLayout()
        lbl_title = QLabel("SETTINGS")
        title_font = QFont("Press Start 2P")
        title_font.setPixelSize(14)
        lbl_title.setFont(title_font)
        lbl_title.setStyleSheet(f"color: {config.COLOR_BTN_PRIMARY_BG}; font-weight: bold;")
        
        btn_close = PixelButton("X", is_primary=False)
        btn_close.setFixedSize(24, 24)
        btn_close.clicked.connect(self.reject)
        
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        title_layout.addWidget(btn_close)
        
        layout.addLayout(title_layout)
        
        # --- Divider ---
        divider = QWidget()
        divider.setFixedHeight(4)
        divider.setStyleSheet(f"background-color: {config.COLOR_BORDER};")
        layout.addWidget(divider)
        
        # --- Form ---
        rem_layout = QHBoxLayout()
        lbl_rem = QLabel("Reminder (min):")
        self.rem_spin = QSpinBox()
        self.rem_spin.setRange(1, 1440)
        self.rem_spin.setValue(rem_min)
        self.rem_spin.setFont(retro_font)
        self.rem_spin.setFixedWidth(70)
        rem_layout.addWidget(lbl_rem)
        rem_layout.addWidget(self.rem_spin)
        layout.addLayout(rem_layout)
        
        snooze_layout = QHBoxLayout()
        lbl_snooze = QLabel("Snooze (min):")
        self.snooze_spin = QSpinBox()
        self.snooze_spin.setRange(1, 60)
        self.snooze_spin.setValue(snooze_min)
        self.snooze_spin.setFont(retro_font)
        self.snooze_spin.setFixedWidth(70)
        snooze_layout.addWidget(lbl_snooze)
        snooze_layout.addWidget(self.snooze_spin)
        layout.addLayout(snooze_layout)
        
        layout.addStretch()
        
        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_save = PixelButton("Save", is_primary=True)
        self.btn_save.clicked.connect(self.save_settings)
        
        self.btn_cancel = PixelButton("Cancel", is_primary=False)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        main_layout.addWidget(container)
        
    def save_settings(self):
        new_rem_ms = self.rem_spin.value() * 60000
        new_snooze_ms = self.snooze_spin.value() * 60000
        
        settings = {
            "reminder_interval_ms": new_rem_ms,
            "snooze_interval_ms": new_snooze_ms
        }
        
        try:
            with open(config.SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")
            return
            
        if self.on_save_callback:
            self.on_save_callback(new_rem_ms, new_snooze_ms)
            
        self.accept()

    # --- Mouse events for dragging the frameless window ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = None
        event.accept()
