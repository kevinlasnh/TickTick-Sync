# -*- coding: utf-8 -*-
"""
Test updating task via TickTick API directly (bypass local client).
"""
import sqlite3
import os
import requests
import json
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'

# Get token and current task content from local DB
conn = sqlite3.connect(str(TICKTICK_DB_PATH))
cursor = conn.cursor()

cursor.execute("SELECT token FROM UserModel LIMIT 1")
token = cursor.fetchone()[0]

cursor.execute("SELECT id, projectId, content FROM TaskModel WHERE title = '个人数据库系统开发日志'")
task_id, project_id, local_content = cursor.fetchone()
conn.close()

print(f"Task ID: {task_id}")
print(f"Project ID: {project_id}")
print(f"Local content has 'test_4': {'test_4' in (local_content or '')}")

# First, GET the current cloud version
headers = {
    'Cookie': f't={token}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'x-device': '{"platform":"web","os":"Windows 10","device":"Chrome 131.0.0.0","name":"","version":6020,"id":"0","channel":"website","campaign":"","websocket":""}',
}

# Get current cloud task
print("\n=== Getting cloud version ===")
resp = requests.get(
    f'https://api.dida365.com/api/v2/task/{task_id}',
    headers=headers,
    timeout=30
)
if resp.status_code == 200:
    cloud_task = resp.json()
    print(f"Cloud content has 'test_4': {'test_4' in (cloud_task.get('content') or '')}")
    print(f"Cloud modifiedTime: {cloud_task.get('modifiedTime')}")
    
    # Now try to UPDATE the cloud version with local content
    print("\n=== Updating cloud version ===")
    
    # Prepare update payload
    update_payload = {
        "id": task_id,
        "projectId": project_id,
        "content": local_content,
    }
    
    # Try batch update endpoint
    batch_url = 'https://api.dida365.com/api/v2/batch/task'
    batch_payload = {
        "update": [update_payload]
    }
    
    print(f"Sending to: {batch_url}")
    resp = requests.post(
        batch_url,
        headers=headers,
        json=batch_payload,
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
else:
    print(f"GET failed: {resp.status_code} - {resp.text}")
