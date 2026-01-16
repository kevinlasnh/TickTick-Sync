# -*- coding: utf-8 -*-
"""
TickTick Sync System Tray Application - Cloud API Version
Wraps daemon.py in a GUI-less tray icon.
"""
import threading
import os
import sys
import logging
import time
import winreg
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from watchdog.observers import Observer

# Import our daemon logic
from daemon import CloudSyncDaemon, LOCAL_DOC_DIR, POLL_INTERVAL, logger

# Status Flags
running = False
observer = None
daemon_thread = None
daemon_instance = None

def create_image():
    """Create a high-quality icon image programmatically."""
    # Create large image for anti-aliasing
    size = 256
    padding = 40
    
    # Brand Colors
    bg_color = (66, 133, 244)  # TickTick/Google Blue
    white = (255, 255, 255)
    
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # 1. Background Circle
    dc.ellipse((10, 10, size-10, size-10), fill=bg_color)
    
    # 2. Cloud Icon (Centered)
    c_center_x = size // 2
    c_center_y = size // 2
    
    # Main central circle
    dc.ellipse((c_center_x - 50, c_center_y - 60, c_center_x + 50, c_center_y + 40), fill=white)
    # Left circle
    dc.ellipse((c_center_x - 90, c_center_y - 20, c_center_x - 10, c_center_y + 60), fill=white)
    # Right circle
    dc.ellipse((c_center_x + 10, c_center_y - 20, c_center_x + 90, c_center_y + 60), fill=white)
    # Bottom filler
    dc.rectangle((c_center_x - 60, c_center_y + 10, c_center_x + 60, c_center_y + 60), fill=white)
    
    # Resize down to 64x64 for smooth edges (Anti-aliasing)
    return image.resize((64, 64), Image.Resampling.LANCZOS)

def run_sync_loop(daemon):
    """The background polling loop."""
    global running
    logger.info("♻️ Cloud sync loop started")
    while running:
        try:
            daemon.pull_from_cloud()
        except Exception as e:
            logger.error(f"Poll error: {e}")
        # Use short sleep intervals to respond quickly to stop signal
        # 使用短间隔 sleep 以快速响应停止信号
        for _ in range(POLL_INTERVAL * 10):  # 10 checks per second
            if not running:
                break
            time.sleep(0.1)
    logger.info("🛑 Cloud sync loop stopped")

def start_sync(icon, item):
    """Start the sync process."""
    global running, observer, daemon_thread, daemon_instance
    
    if running:
        return

    running = True
    
    # Setup CloudSyncDaemon
    try:
        daemon_instance = CloudSyncDaemon()
        
        # Setup Watchdog
        observer = Observer()
        observer.schedule(daemon_instance, str(LOCAL_DOC_DIR), recursive=True)
        observer.start()
        
        # Setup Polling Thread
        daemon_thread = threading.Thread(target=run_sync_loop, args=(daemon_instance,))
        daemon_thread.daemon = True
        daemon_thread.start()
        
        # Force menu refresh
        if icon:
            icon.update_menu()
        
        try:
            icon.notify("TickTick Sync Started", "Cloud API Mode Active")
        except:
            pass  # Notification may fail on some systems
    except Exception as e:
        logger.error(f"Failed to start sync: {e}")
        running = False
        try:
            icon.notify("Start Failed", str(e))
        except:
            pass

def stop_sync(icon, item):
    """Stop the sync process."""
    global running, observer
    
    if not running:
        return

    running = False
    if observer:
        try:
            observer.stop()
            observer.join()
        except Exception as e:
            logger.error(f"Error checking observer: {e}")
    
    # Force menu refresh
    if icon:
        icon.update_menu()
    
    try:
        icon.notify("TickTick Sync Stopped", "Sync Paused")
    except:
        pass

def exit_app(icon, item):
    """Exit the application."""
    stop_sync(icon, item)
    icon.stop()

def open_folder(icon, item):
    """Open the sync folder."""
    os.startfile(LOCAL_DOC_DIR)

# --- Auto-Start Management / 开机自启动管理 ---
AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_KEY_NAME = "TickTickSync"

def get_autostart_command() -> str:
    """Get the command to run this script at startup."""
    # Use pythonw.exe for silent execution (no console window)
    python_exe = sys.executable
    if python_exe.endswith('python.exe'):
        pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
        if os.path.exists(pythonw_exe):
            python_exe = pythonw_exe
    script_path = os.path.abspath(__file__)
    return f'"{python_exe}" "{script_path}"'

def is_autostart_enabled() -> bool:
    """Check if autostart is enabled in registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, AUTOSTART_KEY_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False

def enable_autostart():
    """Enable autostart by adding registry entry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, AUTOSTART_KEY_NAME, 0, winreg.REG_SZ, get_autostart_command())
        winreg.CloseKey(key)
        logger.info("✅ Autostart enabled")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to enable autostart: {e}")
        return False

def disable_autostart():
    """Disable autostart by removing registry entry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, AUTOSTART_KEY_NAME)
        winreg.CloseKey(key)
        logger.info("✅ Autostart disabled")
        return True
    except FileNotFoundError:
        return True  # Already disabled
    except Exception as e:
        logger.error(f"❌ Failed to disable autostart: {e}")
        return False

def toggle_autostart(icon, item):
    """Toggle autostart setting."""
    if is_autostart_enabled():
        disable_autostart()
    else:
        enable_autostart()
    icon.update_menu()

def main():
    image = create_image()
    
    # Dynamic menu item callbacks for real-time status updates
    def get_status_text(item):
        """Dynamic status text - called each time menu is opened."""
        return "Status: [ON] Running" if running else "Status: [OFF] Paused"
    
    def is_running(item):
        """Check if sync is running."""
        return running
    
    def is_paused(item):
        """Check if sync is paused."""
        return not running
    
    # Autostart menu callbacks
    def get_autostart_text(item):
        """Dynamic autostart menu text."""
        if is_autostart_enabled():
            return "Start with Windows: [ON]"
        else:
            return "Start with Windows: [OFF]"
    
    def autostart_checked(item):
        """Check state for autostart menu item."""
        return is_autostart_enabled()
    
    # Build menu with dynamic items
    menu = pystray.Menu(
        # Dynamic status text using callable
        pystray.MenuItem(get_status_text, lambda i, item: None, enabled=False),
        pystray.Menu.SEPARATOR,
        # Show/hide based on current state using 'visible' callback
        pystray.MenuItem('Pause Sync', stop_sync, visible=is_running),
        pystray.MenuItem('Resume Sync', start_sync, visible=is_paused),
        pystray.MenuItem('Open Folder', open_folder),
        pystray.Menu.SEPARATOR,
        # Autostart toggle with checkmark
        pystray.MenuItem(get_autostart_text, toggle_autostart, checked=autostart_checked),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Exit', exit_app)
    )

    icon = pystray.Icon("TickTickSync", image, "TickTick Sync (Cloud API)", menu=menu)
    
    # Auto-start on launch
    t = threading.Timer(1.0, lambda: start_sync(icon, None))
    t.start()
    
    icon.run()

if __name__ == '__main__':
    main()
