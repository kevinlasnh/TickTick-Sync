# -*- coding: utf-8 -*-
"""Check for API tokens in TickTick database."""
import sqlite3
import os
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()

# Check UserModel for tokens
print("=== UserModel ===")
cursor.execute("PRAGMA table_info(UserModel)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

cursor.execute("SELECT * FROM UserModel LIMIT 1")
row = cursor.fetchone()
if row:
    cursor.execute("PRAGMA table_info(UserModel)")
    cols = [c[1] for c in cursor.fetchall()]
    for i, col in enumerate(cols):
        if 'token' in col.lower() or 'auth' in col.lower() or 'key' in col.lower() or 'secret' in col.lower():
            print(f"\n{col}: {str(row[i])[:100]}...")

# Check UserInfoModel
print("\n=== UserInfoModel ===")
cursor.execute("PRAGMA table_info(UserInfoModel)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

conn.close()
