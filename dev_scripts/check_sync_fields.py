# -*- coding: utf-8 -*-
"""
Compare specific sync-related fields before/after TickTick restart.
"""
import sqlite3
import os
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()

# Get column names for SettingsModel
cursor.execute("PRAGMA table_info(SettingsModel)")
columns = [col[1] for col in cursor.fetchall()]

# Get current values
cursor.execute("SELECT * FROM SettingsModel")
row = cursor.fetchone()

print("=== Key Sync-Related Fields ===\n")

# Print sync-related fields
sync_fields = ['SyncPoint', 'CheckPoint', 'PreferrenceMTime', 'LastCheckSyncDate', 
               'CheckRemindDate', 'UpgradeCheckPoint', 'ExtraSettings']
               
for field in sync_fields:
    if field in columns:
        idx = columns.index(field)
        value = row[idx]
        print(f"{field}: {value}")

# Also check SyncStatusModel
print("\n=== SyncStatusModel ===")
cursor.execute("SELECT * FROM SyncStatusModel")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
