# -*- coding: utf-8 -*-
"""Test pull API endpoint."""
import sqlite3
import os
import requests
from pathlib import Path

TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'
API_BASE = 'https://api.dida365.com/api/v2'

# Get token
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

# Test different endpoints
print("=== Testing Pull Endpoints ===\n")

# Try inbox tasks
endpoints = [
    f'{API_BASE}/project/inbox1018769940/tasks',
    f'{API_BASE}/batch/check/0',  # Check for updates since checkpoint 0
    f'{API_BASE}/project/all/tasks',
]

for endpoint in endpoints:
    print(f"Testing: {endpoint}")
    try:
        resp = requests.get(endpoint, headers=headers, timeout=30)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"  Tasks count: {len(data)}")
                # Check for notes
                notes = [t for t in data if t.get('kind') == 'NOTE']
                print(f"  Notes count: {len(notes)}")
                if notes:
                    print(f"  Sample note: {notes[0].get('title', 'no title')[:50]}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}")
        else:
            print(f"  Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
