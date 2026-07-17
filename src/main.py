import os
import sys

# Insert project root into sys.path to allow absolute imports when running directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QTimer
import src.config as config
from src.animation import AnimationManager
from src.controller import WaterCatController

def toggle_windows_startup(enable):
    """Registers or unregisters the application from Windows HKCU startup registry key."""
    if sys.platform != "win32":
        print("Startup registration is only supported on Windows.")
        return
        
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        # Open the registry key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        
        if enable:
            # Command to run: pythonw.exe or python.exe + script path
            exe_path = sys.executable
            # If running as standard python, check if we should run pythonw to hide console window.
            # But standard executable works.
            script_path = os.path.abspath(sys.argv[0])
            # If it's compiled or run directly, write path
            cmd = f'"{exe_path}" "{script_path}" --silent'
            winreg.SetValueEx(key, "WaterCat", 0, winreg.REG_SZ, cmd)
            print("Successfully registered WaterCat in Windows Startup.")
        else:
            try:
                winreg.DeleteValue(key, "WaterCat")
                print("Successfully removed WaterCat from Windows Startup.")
            except FileNotFoundError:
                print("WaterCat registry key not found.")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error configuring startup registry key: {e}")

def main():
    # Setup Argument Parser
    parser = argparse.ArgumentParser(description="WaterCat - Retro Pixel-Art Hydration Reminder")
    parser.add_argument("--test", action="store_true", help="Run in test mode (10s reminders, 5s snooze)")
    parser.add_argument("--interval", type=float, help="Reminder interval in minutes")
    parser.add_argument("--snooze", type=float, help="Snooze interval in minutes")
    parser.add_argument("--startup-enable", action="store_true", help="Register WaterCat to run on Windows startup")
    parser.add_argument("--startup-disable", action="store_true", help="Remove WaterCat from Windows startup")
    parser.add_argument("--silent", action="store_true", help="Launch silently in tray (default)")
    
    args = parser.parse_args()
    
    # Handle startup registration flags first
    if args.startup_enable:
        toggle_windows_startup(True)
        sys.exit(0)
    elif args.startup_disable:
        toggle_windows_startup(False)
        sys.exit(0)
        
    # Start QApplication
    app = QApplication(sys.argv)
    
    # CRITICAL: Prevent application from quitting when reminder window closes
    app.setQuitOnLastWindowClosed(False)
    
    # Load Retro Pixel Font
    if os.path.exists(config.FONT_PATH):
        font_id = QFontDatabase.addApplicationFont(config.FONT_PATH)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"Loaded font families: {families}")
        else:
            print("Failed to load Press Start 2P font.")
    else:
        print(f"Font file not found at: {config.FONT_PATH}")
        
    # Initialize Core Managers
    anim_manager = AnimationManager()
    controller = WaterCatController(anim_manager, app)
    
    # Apply Command Line Argument Configurations
    reminder_ms = config.DEFAULT_REMINDER_INTERVAL
    snooze_ms = config.DEFAULT_SNOOZE_INTERVAL
    
    if args.test:
        print("Running in TEST mode (reminders = 10s, snooze = 5s)")
        reminder_ms = 10 * 1000      # 10 seconds
        snooze_ms = 5 * 1000         # 5 seconds
    else:
        if args.interval:
            reminder_ms = int(args.interval * 60 * 1000)
        if args.snooze:
            snooze_ms = int(args.snooze * 60 * 1000)
            
    controller.set_intervals(reminder_ms, snooze_ms)
    
    # If not running silently (or just to trigger immediate popup on launch for testing)
    if args.test:
        # Trigger reminder quickly after launch
        QTimer.singleShot(1000, controller.trigger_reminder)
        
    # Start Qt Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
