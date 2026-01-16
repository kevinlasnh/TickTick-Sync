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
    """Create a simple icon image programmatically."""
    width = 64
    height = 64
    # Blue gradient for cloud sync
    color1 = (66, 133, 244)  # Google Blue
    color2 = (255, 255, 255)  # White

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    # Cloud-like shape
    dc.ellipse((10, 25, 35, 50), fill=color2)
    dc.ellipse((25, 20, 55, 50), fill=color2)
    dc.ellipse((40, 25, 60, 48), fill=color2)
    dc.rectangle((15, 35, 55, 50), fill=color2)
    return image

def run_sync_loop(daemon):
    """The background polling loop."""
    global running
    logger.info("♻️ Cloud sync loop started")
    while running:
        try:
            daemon.pull_from_cloud()
        except Exception as e:
            logger.error(f"Poll error: {e}")
        time.sleep(POLL_INTERVAL)
    logger.info("🛑 Cloud sync loop stopped")

def start_sync(icon, item):
    """Start the sync process."""
    global running, observer, daemon_thread, daemon_instance
    
    if running:
        return

    running = True
    
    # Setup CloudSyncDaemon
    daemon_instance = CloudSyncDaemon()
    
    # Setup Watchdog
    observer = Observer()
    observer.schedule(daemon_instance, str(LOCAL_DOC_DIR), recursive=True)
    observer.start()
    
    # Setup Polling Thread
    daemon_thread = threading.Thread(target=run_sync_loop, args=(daemon_instance,))
    daemon_thread.daemon = True
    daemon_thread.start()
    
    try:
        icon.notify("TickTick Sync Started", "☁️ Cloud API Mode Active")
    except:
        pass  # Notification may fail on some systems

def stop_sync(icon, item):
    """Stop the sync process."""
    global running, observer
    
    if not running:
        return

    running = False
    if observer:
        observer.stop()
        observer.join()
    
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

def main():
    image = create_image()
    
    menu = pystray.Menu(
        pystray.MenuItem('Start Sync', start_sync, checked=lambda item: running),
        pystray.MenuItem('Stop Sync', stop_sync, checked=lambda item: not running),
        pystray.MenuItem('Open Folder', open_folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Exit', exit_app)
    )

    icon = pystray.Icon("TickTickSync", image, "TickTick Sync (Cloud API)", menu)
    
    # Auto-start on launch
    t = threading.Timer(1.0, lambda: start_sync(icon, None))
    t.start()
    
    icon.run()

if __name__ == '__main__':
    main()
