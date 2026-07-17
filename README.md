# WaterCat 🐱💧

WaterCat is a retro pixel-art desktop companion and hydration reminder application built in Python using PySide6. 
It runs silently in the system tray and pops up every hour, featuring a cute cat companion that walks onto the screen, speech-bubbles you to drink water, and reacts dynamically to your choices!

---

## Features

1. **Silent Background Daemon**: Starts up quietly and sits in the system tray.
2. **Dynamic UI Rendering**: Frameless, transparent floating window positioned at the bottom-right corner of the primary screen.
3. **Nearest-Neighbor Scaling**: Sprites are rendered with crisp, retro pixel-art fidelity.
4. **Custom Retro UI Widgets**: Programmable speech bubbles with stair-step corners and custom-styled pixel buttons.
5. **State-Driven Interactions**:
   - **I Drank Water**: The cat plays a drinking animation, celebrates happily, and walks off the screen.
   - **Snooze 5 Minutes**: The cat shows a sad reaction, falls asleep on the desktop, and wakes up after 5 minutes to remind you again.
6. **Automatic Sprite Processor**: Automatically strips off-white/light-gray background checkerboards from sprite sheets and caches transparent PNGs dynamically.
7. **Windows Startup Registration**: Easy command-line flag to register/unregister the app in Windows Startup.

---

## Installation

1. Make sure Python 3.10+ is installed on your system.
2. Open a terminal (PowerShell or Command Prompt) and navigate to the project directory:
   ```powershell
   cd C:\Hrudya\Projects\WaterCat
   ```
3. Install the dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## Running the Application

### 1. Normal Mode (Production)
Runs silently in the background with a 1-hour reminder timer and 5-minute snooze.
```powershell
python src/main.py
```
*You can access the WaterCat icon in your Windows System Tray to manually trigger a reminder ("Remind Now"), reset the timer, or exit.*

### 2. Test Mode (Quick Validation)
Speeds up the intervals for quick testing (reminds every 10 seconds, snoozes for 5 seconds). Triggers the first reminder 1 second after startup.
```powershell
python src/main.py --test
```

### 3. Custom Intervals
Configure custom intervals in minutes:
```powershell
python src/main.py --interval 30 --snooze 2
```
*(Reminds every 30 minutes, snoozes for 2 minutes)*

### 4. Windows Startup Registration
To have WaterCat launch automatically in the background when Windows starts:
```powershell
python src/main.py --startup-enable
```
To remove it from Windows startup:
```powershell
python src/main.py --startup-disable
```

---

## Project Structure

- `assets/`: Contains raw sprite sheets and the bundled OFL Press Start 2P pixel font.
- `assets/.cache/`: Directory generated dynamically containing processed, transparent PNG sprite sheets.
- `src/main.py`: Application entry point, CLI arguments, and system tray initialization.
- `src/config.py`: Global styling tokens, timing defaults, and sprite configurations.
- `src/controller.py`: Core state machine, timer loops, and tray context menu coordination.
- `src/animation.py`: Checkerboard background remover and animation frame coordinate slicer.
- `src/ui/`: UI components.
  - `reminder_window.py`: Frameless transparent desktop window container.
  - `cat_widget.py`: Custom paint canvas drawing the scaled sprite frame.
  - `bubble.py`: Custom speech bubble drawn programmatically with blocky stair-step corners.
  - `button.py`: Custom pixel buttons with hover/press stylesheet animations.
