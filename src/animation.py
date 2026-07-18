import os
import glob
import numpy as np
from PIL import Image
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QObject, Signal, QTimer, Qt
import src.config as config


class AnimationManager(QObject):
    """Loads individual frame images from folders, makes them transparent, and ticks through them."""
    frame_changed      = Signal(QPixmap)  # emitted every frame-timer tick
    animation_finished = Signal()         # emitted when a non-looping animation ends

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_dir = os.path.join(config.ASSETS_DIR, ".cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Dict[str, list[QPixmap]]
        self.animations: dict[str, list] = {}
        self._load_all()

        # Playback state
        self.current_animation  = None
        self.current_frames     = []
        self.current_frame_index = 0
        self.loop               = True

        # Animation timer — ONLY changes frame index
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._next_frame)
        self.timer.setInterval(config.FRAME_DURATION_MS)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _load_all(self):
        for name, cfg in config.SPRITE_CONFIGS.items():
            folder_name = cfg.get("folder", name)
            folder_path = os.path.join(config.ASSETS_DIR, folder_name)

            if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
                print(f"Warning: Folder {folder_path} not found, skipping animation '{name}'.")
                continue

            # Load all png/jpg files in alphabetical order
            file_paths = []
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                file_paths.extend(glob.glob(os.path.join(folder_path, ext)))
            
            file_paths.sort()  # Ensure correct frame order (000.png, 001.png, etc.)
            
            if "frame_indices" in cfg:
                indices = cfg["frame_indices"]
                file_paths = [file_paths[i] for i in indices if i < len(file_paths)]
            elif "max_frames" in cfg:
                file_paths = file_paths[:cfg["max_frames"]]

            frames = []
            for path in file_paths:
                # Generate unique cache path for this frame
                filename = os.path.basename(path)
                cache_name = f"{folder_name}_{filename}.png"
                cache_path = os.path.join(self.cache_dir, cache_name)

                # Process background if needed
                if not os.path.exists(cache_path) or os.path.getmtime(path) > os.path.getmtime(cache_path):
                    self._make_transparent(path, cache_path)

                pixmap = QPixmap(cache_path)
                if not pixmap.isNull():
                    # Scale to fit standard target dimensions so large assets don't get cropped
                    scaled_pixmap = pixmap.scaled(config.TARGET_WIDTH, config.TARGET_HEIGHT, 
                                                  Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    frames.append(scaled_pixmap)

            if frames:
                self.animations[name] = frames
                print(f"Loaded animation '{name}': {len(frames)} frames, "
                      f"size {frames[0].width()}x{frames[0].height()}")
            else:
                print(f"Warning: No valid images found in {folder_path} for animation '{name}'.")

    # ------------------------------------------------------------------
    # Background Removal
    # ------------------------------------------------------------------
    def _make_transparent(self, src_path, dest_path):
        img = Image.open(src_path).convert("RGBA")
        data = np.array(img)
        alpha = data[:, :, 3]

        if np.any(alpha < 255):
            # Already transparent — save as-is
            img.save(dest_path, "PNG")
            return

        # BFS flood-fill from borders to remove dark/black background
        h, w = data.shape[:2]
        gray = np.mean(data[:, :, :3], axis=2)
        threshold = 30
        is_bg = gray < threshold
        visited = np.zeros((h, w), dtype=bool)

        queue = []
        for x in range(w):
            for row in (0, h - 1):
                if is_bg[row, x] and not visited[row, x]:
                    visited[row, x] = True
                    queue.append((row, x))
        for y in range(1, h - 1):
            for col in (0, w - 1):
                if is_bg[y, col] and not visited[y, col]:
                    visited[y, col] = True
                    queue.append((y, col))

        idx = 0
        while idx < len(queue):
            cy, cx = queue[idx]; idx += 1
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and is_bg[ny, nx]:
                    visited[ny, nx] = True
                    queue.append((ny, nx))

        data[visited, 3] = 0
        
        # --- Vertical Alignment (Baseline Fix) ---
        alpha_channel = data[:, :, 3]
        # Find all Y coordinates where pixel is not fully transparent
        y_coords = np.where(alpha_channel > 0)[0]
        if len(y_coords) > 0:
            lowest_y = y_coords.max()
            target_y = h - 2  # Align 1 pixel above the absolute bottom edge
            dy = target_y - lowest_y
            
            if dy != 0:
                new_data = np.zeros_like(data)
                if dy > 0:
                    new_data[dy:, :, :] = data[:-dy, :, :]
                elif dy < 0:
                    new_data[:dy, :, :] = data[-dy:, :, :]
                data = new_data
                
        Image.fromarray(data, "RGBA").save(dest_path, "PNG")

    # ------------------------------------------------------------------
    # Playback API
    # ------------------------------------------------------------------
    def play(self, name: str, loop: bool = True, interval_ms: int = None):
        if name not in self.animations:
            print(f"Error: animation '{name}' not found.")
            return
        self.current_animation   = name
        self.current_frames      = self.animations[name]
        self.current_frame_index = 0
        self.loop                = loop
        self.timer.setInterval(interval_ms or config.FRAME_DURATION_MS)
        self.timer.start()
        # Emit frame 0 immediately so the sprite updates without waiting
        if self.current_frames:
            self.frame_changed.emit(self.current_frames[0])

    def stop(self):
        self.timer.stop()

    def get_current_frame(self) -> QPixmap:
        if not self.current_frames:
            return QPixmap()
        return self.current_frames[self.current_frame_index]

    # ------------------------------------------------------------------
    # Timer slot — ONLY changes frame index, never touches position
    # ------------------------------------------------------------------
    def _next_frame(self):
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
