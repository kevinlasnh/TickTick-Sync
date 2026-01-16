# -*- coding: utf-8 -*-
"""Analyze specific task structure from API."""
import sqlite3
import os
import requests
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'
API_BASE = 'https://api.dida365.com/api/v2'

conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()
cursor.execute("SELECT token FROM UserModel LIMIT 1")
token = cursor.fetchone()[0]
conn.close()

headers = {
    'Cookie': f't={token}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
}

# Get test task
try:
    resp = requests.get(f'{API_BASE}/project/inbox1018769940/tasks', headers=headers, timeout=30)
    print(f"Status Code: {resp.status_code}")
    tasks = resp.json()
except Exception as e:
    print(f"Error: {e}")
    print(f"Response Text: {resp.text[:500]}")
    exit(1)

# Find our test task
for task in tasks:
    if '个人数据库系统开发日志' in task.get('title', ''):
        print("=== Task Structure ===")
        for key, value in task.items():
            val_str = str(value)[:100] if value else 'None'
            print(f"  {key}: {val_str}")
        
        print("\n=== Content Check ===")
        content = task.get('content', '')
        print(f"Has 'test_5': {'test_5' in content}")
        print(f"Has 'test_6': {'test_6' in content}")
        print(f"modifiedTime: {task.get('modifiedTime')}")
        break
