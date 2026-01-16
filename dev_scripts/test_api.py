# -*- coding: utf-8 -*-
"""
Test direct API call to TickTick with extracted token.
"""
import sqlite3
import os
import requests
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

# Get token and task info
conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()

cursor.execute("SELECT token FROM UserModel LIMIT 1")
token = cursor.fetchone()[0]
print(f"Token (first 50 chars): {token[:50]}...")

cursor.execute("SELECT id, title, projectId FROM TaskModel WHERE title = '个人数据库系统开发日志'")
task_id, title, project_id = cursor.fetchone()
print(f"Task ID: {task_id}")
print(f"Project ID: {project_id}")

conn.close()

# Try calling TickTick API
# Note: TickTick uses different API endpoints
# - api.ticktick.com for international
# - api.dida365.com for China
# Let's try both

headers = {
    'Cookie': f't={token}',
    'Content-Type': 'application/json',
    'User-Agent': 'TickTick'
}

# Try to trigger a sync by fetching task (may refresh cache)
endpoints = [
    f'https://api.ticktick.com/api/v2/task/{task_id}',
    f'https://api.dida365.com/api/v2/task/{task_id}',
]

for endpoint in endpoints:
    print(f"\nTrying: {endpoint}")
    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:200]}...")
        else:
            print(f"  Response: {resp.text[:100]}")
    except Exception as e:
        print(f"  Error: {e}")
