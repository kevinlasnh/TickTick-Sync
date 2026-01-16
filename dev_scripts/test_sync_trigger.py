# -*- coding: utf-8 -*-
"""
Test: Insert into SyncStatusModel to trigger sync
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()

# Get user ID and task ID
cursor.execute("SELECT UserId FROM SettingsModel LIMIT 1")
user_id = cursor.fetchone()[0]
print(f"User ID: {user_id}")

cursor.execute("SELECT id FROM TaskModel WHERE title = '个人数据库系统开发日志'")
task_id = cursor.fetchone()[0]
print(f"Task ID: {task_id}")

# Get current ModifyPoint (timestamp in some format)
modify_point = int(datetime.now().timestamp() * 1000)
print(f"ModifyPoint: {modify_point}")

# Insert into SyncStatusModel
# Type: guessing 1 = Task update, based on common patterns
try:
    cursor.execute("""
        INSERT INTO SyncStatusModel (UserId, EntityId, MoveFromId, OldParentId, Type, ModifyPoint)
        VALUES (?, ?, '', '', 1, ?)
    """, (user_id, task_id, modify_point))
    conn.commit()
    print("✅ Inserted sync entry!")
    
    # Verify
    cursor.execute("SELECT * FROM SyncStatusModel")
    print(f"SyncStatusModel entries: {cursor.fetchall()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Also try updating SyncPoint in SettingsModel
try:
    cursor.execute("UPDATE SettingsModel SET SyncPoint = ?", (modify_point,))
    conn.commit()
    print("✅ Updated SyncPoint in SettingsModel!")
except Exception as e:
    print(f"❌ SyncPoint update error: {e}")

conn.close()
print("\n🔍 Now check if TickTick syncs to cloud...")
