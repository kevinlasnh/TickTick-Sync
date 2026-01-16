# -*- coding: utf-8 -*-
"""
Analyze SyncPoint format and test sync trigger.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

# .NET ticks to datetime conversion
# .NET ticks = 100-nanosecond intervals since 0001-01-01
# Python datetime epoch is 1970-01-01
# Difference: 621355968000000000 ticks

def ticks_to_datetime(ticks):
    """Convert .NET ticks to Python datetime."""
    epoch_diff = 621355968000000000  # Ticks between 0001-01-01 and 1970-01-01
    seconds = (ticks - epoch_diff) / 10000000
    return datetime.utcfromtimestamp(seconds)

def datetime_to_ticks(dt):
    """Convert Python datetime to .NET ticks."""
    epoch_diff = 621355968000000000
    seconds = dt.timestamp()
    return int(seconds * 10000000 + epoch_diff)

# Get current SyncPoint
conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()
cursor.execute("SELECT SyncPoint FROM SettingsModel")
current_syncpoint = cursor.fetchone()[0]
conn.close()

print("=== SyncPoint Analysis ===\n")
print(f"Current SyncPoint: {current_syncpoint}")

try:
    dt = ticks_to_datetime(current_syncpoint)
    print(f"As datetime: {dt}")
except Exception as e:
    print(f"Failed to parse as .NET ticks: {e}")

# Generate new SyncPoint for "now"
now_ticks = datetime_to_ticks(datetime.utcnow())
print(f"\nCurrent time as ticks: {now_ticks}")
