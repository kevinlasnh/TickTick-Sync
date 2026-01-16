# -*- coding: utf-8 -*-
"""Deep dive into SyncStatusModel"""
import sqlite3
import os
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()

# Check SyncStatusModel structure and data
print("=== SyncStatusModel ===")
cursor.execute("PRAGMA table_info(SyncStatusModel)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

cursor.execute("SELECT * FROM SyncStatusModel LIMIT 10")
rows = cursor.fetchall()
print(f"\nSample entries ({len(rows)} shown):")
for row in rows:
    print(f"  {row}")

# Check if our task has an entry
print("\n=== Looking for test task ===")
cursor.execute("SELECT id FROM TaskModel WHERE title = '个人数据库系统开发日志'")
task_id = cursor.fetchone()[0]
print(f"Task ID: {task_id}")

cursor.execute("SELECT * FROM SyncStatusModel WHERE EntityId = ?", (task_id,))
sync_entry = cursor.fetchone()
print(f"SyncStatusModel entry: {sync_entry}")

# Check SettingsModel sync fields
print("\n=== SettingsModel Sync Fields ===")
cursor.execute("SELECT SyncPoint, CheckPoint, PreferrenceMTime FROM SettingsModel")
row = cursor.fetchone()
print(f"SyncPoint: {row[0]}")
print(f"CheckPoint: {row[1]}")
print(f"PreferrenceMTime: {row[2]}")

conn.close()
