import os
import numpy as np
from PIL import Image
from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtCore import QObject, Signal, QTimer, Qt
import src.config as config

class AnimationManager(QObject):
    """Manages sprite sheet processing, transparency caching, and frame playback."""
    frame_changed = Signal(QPixmap)  # Emitted when a new frame is ready
    animation_finished = Signal()     # Emitted when a non-looping animation finishes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_dir = os.path.join(config.ASSETS_DIR, ".cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load and slice all animations
        self.animations = {}
        self.load_all_animations()
        
        # Playback state
        self.current_animation = None
        self.current_frames = []
        self.current_frame_index = 0
        self.loop = True
        
        # Timer for frame updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.setInterval(config.FRAME_DURATION_MS)

    def load_all_animations(self):
        """Loads and pre-processes all sprite sheets into transparent frame lists."""
        for anim_name, cfg in config.SPRITE_CONFIGS.items():
            jpg_path = os.path.join(config.ASSETS_DIR, cfg["filename"])
            if not os.path.exists(jpg_path):
                print(f"Warning: Asset {jpg_path} not found!")
                continue
                
            cache_png_path = os.path.join(self.cache_dir, f"{anim_name}.png")
            crop_y = cfg.get("crop_y", None)
            bg_threshold = cfg.get("bg_threshold", 200)
            
            # Regenerate if source JPG is newer than cache or cache doesn't exist
            if not os.path.exists(cache_png_path) or os.path.getmtime(jpg_path) > os.path.getmtime(cache_png_path):
                print(f"Processing background removal for: {cfg['filename']}")
                self.process_checkerboard_removal(jpg_path, cache_png_path, crop_y, bg_threshold)
            
            # Load transparent sprite sheet
            pixmap = QPixmap(cache_png_path)
            if pixmap.isNull():
                print(f"Error loading processed image: {cache_png_path}")
                continue
                
            # Slice into frames
            frames_list = []
            base_w = cfg["base_width"]
            base_h = cfg["base_height"]
            total_frames = cfg["frames"]
            
            for i in range(total_frames):
                x0 = int(i * base_w)
                x1 = int((i + 1) * base_w)
                frame_w = x1 - x0
                
                # Copy the frame rect from sheet
                frame_pixmap = pixmap.copy(x0, 0, frame_w, int(base_h))
                
                # Scale keeping aspect ratio to fit within TARGET_WIDTH x TARGET_HEIGHT
                scaled = frame_pixmap.scaled(
                    config.TARGET_WIDTH,
                    config.TARGET_HEIGHT,
                    Qt.KeepAspectRatio,
                    Qt.FastTransformation
                )
                
                # Create a uniform transparent canvas of target dimensions (128x123)
                canvas = QPixmap(config.TARGET_WIDTH, config.TARGET_HEIGHT)
                canvas.fill(Qt.transparent)
                
                # Paint the scaled sprite onto the canvas aligned at the bottom-center
                painter = QPainter(canvas)
                x = (config.TARGET_WIDTH - scaled.width()) // 2
                y = config.TARGET_HEIGHT - scaled.height()  # Align to bottom baseline
                painter.drawPixmap(x, y, scaled)
                painter.end()
                
                frames_list.append(canvas)
                
            self.animations[anim_name] = frames_list
            print(f"Loaded animation '{anim_name}': {len(frames_list)} frames, size {frames_list[0].width()}x{frames_list[0].height()}")

    def process_checkerboard_removal(self, src_path, dest_path, crop_y=None, bg_threshold=200):
        """Removes the off-white/light-gray checkerboard pattern from the JPEG."""
        img = Image.open(src_path).convert('RGBA')
        
        # Crop vertically first if crop range is specified
        if crop_y:
            y_start, y_end = crop_y
            img = img.crop((0, y_start, img.width, y_end))
            
        w, h = img.size
        data = np.array(img)
        gray = np.mean(data[:, :, :3], axis=2)
        
        # Step 1: Flood fill from borders to identify outer background checkerboard
        # This keeps the white portions inside the cat intact.
        bg_mask = np.zeros((h, w), dtype=bool)
        # Use custom configurable threshold per-sprite-sheet (e.g. 175 for happy2.jpg, 200 for others)
        light_mask = gray > bg_threshold
        
        queue = []
        # Add all border pixels that are light
        for x in range(w):
            if light_mask[0, x]:
                queue.append((0, x))
                bg_mask[0, x] = True
            if light_mask[h-1, x]:
                queue.append((h-1, x))
                bg_mask[h-1, x] = True
        for y in range(1, h-1):
            if light_mask[y, 0]:
                queue.append((y, 0))
                bg_mask[y, 0] = True
            if light_mask[y, w-1]:
                queue.append((y, w-1))
                bg_mask[y, w-1] = True
                
        # BFS traversal
        idx = 0
        while idx < len(queue):
            cy, cx = queue[idx]
            idx += 1
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w:
                    if not bg_mask[ny, nx] and light_mask[ny, nx]:
                        bg_mask[ny, nx] = True
                        queue.append((ny, nx))
                        
        # Apply transparency mask
        data[bg_mask, 3] = 0
        
        # Save transparent PNG
        new_img = Image.fromarray(data, 'RGBA')
        new_img.save(dest_path, 'PNG')

    def play(self, animation_name, loop=True, interval_ms=None):
        """Starts playing the specified animation."""
        if animation_name not in self.animations:
            print(f"Error: Animation '{animation_name}' does not exist!")
            return
            
        self.current_animation = animation_name
        self.current_frames = self.animations[animation_name]
        self.current_frame_index = 0
        self.loop = loop
        
        # Set custom interval if provided, otherwise restore default
        self.timer.setInterval(interval_ms or config.FRAME_DURATION_MS)
        self.timer.start()
        # Emit the first frame immediately
        self.frame_changed.emit(self.current_frames[0])

    def stop(self):
        """Stops animation playback."""
        self.timer.stop()

    def next_frame(self):
        """Timer callback to advance the animation frame."""
        if not self.current_frames:
            return
            
        self.current_frame_index += 1
        
        if self.current_frame_index >= len(self.current_frames):
            if self.loop:
                self.current_frame_index = 0
            else:
                self.current_frame_index = len(self.current_frames) - 1
                self.timer.stop()
                self.animation_finished.emit()
                return
                
        self.frame_changed.emit(self.current_frames[self.current_frame_index])

    def get_current_frame(self):
        """Gets the currently active animation QPixmap."""
        if not self.current_frames:
            return QPixmap()
        return self.current_frames[self.current_frame_index]
