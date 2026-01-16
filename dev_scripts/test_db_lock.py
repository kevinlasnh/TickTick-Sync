# -*- coding: utf-8 -*-
"""
Test if we can write to TickTick DB while app is running.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

print("Testing database access while TickTick is running...\n")

try:
    # Try connecting with timeout
    conn = sqlite3.connect(str(TICKTICK_DB_PATH), timeout=5)
    cursor = conn.cursor()
    
    # Check WAL mode
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    print(f"📊 Journal mode: {mode}")
    
    # Try reading
    cursor.execute("SELECT COUNT(*) FROM TaskModel")
    count = cursor.fetchone()[0]
    print(f"✅ Read success: {count} tasks")
    
    # Try writing (update a note's modifiedTime)
    cursor.execute("""
        SELECT id, title, modifiedTime FROM TaskModel 
        WHERE kind = 'NOTE' LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        task_id, title, old_mtime = row
        new_mtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n🔧 Testing write on: {title}")
        print(f"   Old mtime: {old_mtime}")
        print(f"   New mtime: {new_mtime}")
        
        cursor.execute("""
            UPDATE TaskModel SET modifiedTime = ? WHERE id = ?
        """, (new_mtime, task_id))
        
        conn.commit()
        print("✅ Write success!")
        
        # Restore original
        cursor.execute("""
            UPDATE TaskModel SET modifiedTime = ? WHERE id = ?
        """, (old_mtime, task_id))
        conn.commit()
        print("✅ Restored original mtime")
    
    conn.close()
    print("\n🎉 Database is NOT locked! Real-time sync is possible!")
    
except sqlite3.OperationalError as e:
    print(f"❌ Database locked: {e}")
    print("\nReal-time sync requires closing TickTick first.")
except Exception as e:
    print(f"❌ Error: {e}")
