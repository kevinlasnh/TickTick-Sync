# -*- coding: utf-8 -*-
"""
Monitor TickTick database changes during startup.
Run this script, then restart TickTick to capture what happens.
"""
import sqlite3
import os
import time
from pathlib import Path
from datetime import datetime

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

def get_snapshot():
    """Get current state of key tables."""
    conn = sqlite3.connect(str(TICKTICK_DB_PATH))
    cursor = conn.cursor()
    
    snapshot = {}
    
    # SettingsModel - all fields
    cursor.execute("SELECT * FROM SettingsModel")
    snapshot['SettingsModel'] = cursor.fetchone()
    
    # SyncStatusModel - all entries
    cursor.execute("SELECT * FROM SyncStatusModel")
    snapshot['SyncStatusModel'] = cursor.fetchall()
    
    # TaskModel - just count and last modified
    cursor.execute("SELECT COUNT(*) FROM TaskModel")
    snapshot['TaskModel_count'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(modifiedTime) FROM TaskModel")
    snapshot['TaskModel_lastModified'] = cursor.fetchone()[0]
    
    # Get specific task we modified
    cursor.execute("SELECT modifiedTime, content FROM TaskModel WHERE title = '个人数据库系统开发日志'")
    row = cursor.fetchone()
    snapshot['test_task_mtime'] = row[0] if row else None
    snapshot['test_task_has_test4'] = 'test_4' in (row[1] or '') if row else False
    
    conn.close()
    return snapshot

def compare_snapshots(before, after):
    """Compare two snapshots and print differences."""
    print("\n" + "="*60)
    print(f"CHANGES DETECTED at {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    for key in before:
        if before[key] != after[key]:
            print(f"\n📌 {key}:")
            print(f"   BEFORE: {str(before[key])[:200]}")
            print(f"   AFTER:  {str(after[key])[:200]}")

print("🔍 TickTick Database Monitor")
print("="*60)
print("1. This script will monitor database changes")
print("2. Please RESTART TickTick now")
print("3. Press Ctrl+C to stop monitoring")
print("="*60)

# Take initial snapshot
print(f"\n📸 Initial snapshot at {datetime.now().strftime('%H:%M:%S')}")
last_snapshot = get_snapshot()
print(f"   SyncStatusModel entries: {len(last_snapshot['SyncStatusModel'])}")
print(f"   Task count: {last_snapshot['TaskModel_count']}")
print(f"   Test task has test_4: {last_snapshot['test_task_has_test4']}")

print("\n⏳ Monitoring... (restart TickTick now)")

try:
    while True:
        time.sleep(0.5)  # Check every 500ms
        current = get_snapshot()
        
        if current != last_snapshot:
            compare_snapshots(last_snapshot, current)
            last_snapshot = current
            
except KeyboardInterrupt:
    print("\n\n🛑 Monitoring stopped.")
