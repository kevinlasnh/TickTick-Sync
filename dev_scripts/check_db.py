# -*- coding: utf-8 -*-
"""Check if test_4 exists in DB"""
import sqlite3
import os
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()
cursor.execute("SELECT content FROM TaskModel WHERE title = '个人数据库系统开发日志'")
row = cursor.fetchone()
if row and row[0]:
    content = row[0]
    print("Content length:", len(content))
    print("Contains 'test_4':", 'test_4' in content)
    print("Contains 'test_3':", 'test_3' in content)
    # Print last 200 chars
    print("\nLast 500 chars of content:")
    print(content[-500:] if len(content) > 500 else content)
else:
    print("No content found")
conn.close()
