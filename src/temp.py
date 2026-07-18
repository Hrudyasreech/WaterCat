from PIL import Image
import os

# ==========================
# CONFIG
# ==========================
IMAGE_PATH = r"C:\Users\hrudy\Downloads\Gemini_Generated_Image_j5gmdaj5gmdaj5gm.png"    # AI sprite sheet
OUTPUT_DIR = "assets/happy_dance"

ROWS = 3
COLS = 3

IGNORE_FIRST = True      # Ignore top-left reference cat

# ==========================

os.makedirs(OUTPUT_DIR, exist_ok=True)

img = Image.open(IMAGE_PATH)

sheet_w, sheet_h = img.size

cell_w = sheet_w // COLS
cell_h = sheet_h // ROWS

frame = 0

for r in range(ROWS):
    for c in range(COLS):

        # Skip the reference cat
        if IGNORE_FIRST and r == 0 and c == 0:
            continue

        left = c * cell_w
        top = r * cell_h
        right = left + cell_w
        bottom = top + cell_h

        crop = img.crop((left, top, right, bottom))

        crop.save(
            os.path.join(
                OUTPUT_DIR,
                f"{frame:03}.png"
            )
        )

        frame += 1

print(f"Saved {frame} frames to '{OUTPUT_DIR}'")