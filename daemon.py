# -*- coding: utf-8 -*-
"""
TickTick Real-time Sync Daemon - Cloud API Version
Uses TickTick Cloud API (api.dida365.com) for bidirectional sync.
"""
import sys
import io
import time
import logging
import sqlite3
import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Fix Windows console encoding (only if stdout exists, e.g., not in --noconsole mode)
if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'
LOCAL_DOC_DIR = Path(r'C:\Zero\Doc\Local\Life\Personal_dataBase')
POLL_INTERVAL = 10  # Seconds between cloud checks
API_BASE = 'https://api.dida365.com/api/v2'

# Logging Setup - Use NullHandler if no console available
log_handlers = []
if sys.stdout is not None:
    log_handlers.append(logging.StreamHandler(sys.stdout))
else:
    log_handlers.append(logging.NullHandler())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def get_auth_token() -> str:
    """Extract auth token from local TickTick database."""
    conn = sqlite3.connect(str(TICKTICK_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM UserModel LIMIT 1")
    token = cursor.fetchone()[0]
    conn.close()
    return token

def get_api_headers(token: str) -> dict:
    """Create API request headers."""
    return {
        'Cookie': f't={token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'x-device': '{"platform":"web","os":"Windows 10","device":"Chrome","name":"","version":6020,"id":"0","channel":"website","campaign":"","websocket":""}',
    }

def parse_frontmatter(file_path: Path) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from .md file."""
    if not file_path.exists():
        return {}, ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception:
        return {}, ""
    
    if not text.startswith('---'):
        return {}, text
    end_idx = text.find('---', 3)
    if end_idx == -1:
        return {}, text
    
    frontmatter_str = text[3:end_idx].strip()
    content = text[end_idx + 3:].strip()
    metadata = {}
    for line in frontmatter_str.split('\n'):
        match = re.match(r'^(\w+):\s*(.+)$', line.strip())
        if match:
            key, value = match.groups()
            value = value.strip().strip('"').strip("'")
            metadata[key] = value
    return metadata, content

def sanitize_filename(name: str) -> str:
    """Sanitize filename for Windows."""
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)
    sanitized = sanitized.strip(' .')
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized or 'untitled'

def extract_func_level(tag_list) -> str:
    """Extract func_level tag from tag list."""
    if not tag_list:
        return 'no_tag'
    if isinstance(tag_list, str):
        try:
            tag_list = json.loads(tag_list)
        except:
            return 'no_tag'
    for tag in tag_list:
        if isinstance(tag, str) and tag.startswith('func_level_'):
            return tag
    return 'no_tag'

# --- Core Sync Logic ---

class CloudSyncDaemon(FileSystemEventHandler):
    def __init__(self):
        self.token = get_auth_token()
        self.headers = get_api_headers(self.token)
        self.recently_processed = {}  # Debounce
        self.path_map = {}  # {str(file_path): task_id}
        self.DEBOUNCE_SECONDS = 3
        logger.info("🔑 Auth token loaded")
        self.rebuild_path_map()

    def rebuild_path_map(self):
        """Build initial path->id map from existing files."""
        count = 0
        for file_path in LOCAL_DOC_DIR.rglob('*.md'):
            meta, _ = parse_frontmatter(file_path)
            task_id = meta.get('task_id')
            if task_id:
                self.path_map[str(file_path)] = task_id
                count += 1
        logger.info(f"🗺️ Path map built: {count} items")

    def on_moved(self, event):
        """Handle file rename/move."""
        if event.is_directory or not event.src_path.endswith('.md'):
            return

        src_path = str(Path(event.src_path))
        dest_path = str(Path(event.dest_path))
        
        # Debounce check
        if self.is_debounced(src_path) or self.is_debounced(dest_path):
            return

        logger.info(f"🔄 Detected Move: {Path(src_path).name} -> {Path(dest_path).name}")

        task_id = self.path_map.get(src_path)
        if not task_id:
            logger.warning(f"⚠️ Unknown file moved, treating as new: {dest_path}")
            # Treat as new file
            self.on_modified(event) 
            return

        # Update map
        del self.path_map[src_path]
        self.path_map[dest_path] = task_id

        # Update title in Cloud
        new_title = Path(dest_path).stem
        # Also need to update the file content to reflect new title if we want consistency?
        # For now, just update cloud.
        self.update_task_title(task_id, new_title)
        
        # We also need to update the file's frontmatter 'title' to match filename?
        # That would trigger another modification. Let's leave file content alone for now,
        # or relying on the user to have updated it. 
        # Actually, if user renamed file in Explorer, frontmatter is stale.
        # Ideally we should update frontmatter.

    def on_deleted(self, event):
        """Handle file deletion."""
        if event.is_directory or not event.src_path.endswith('.md'):
            return

        file_path = str(Path(event.src_path))
        
        if self.is_debounced(file_path):
            return

        task_id = self.path_map.get(file_path)
        if task_id:
            logger.info(f"🗑️ Detected Deletion: {Path(file_path).name} (ID: {task_id})")
            self.delete_cloud_task(task_id)
            del self.path_map[file_path]
        else:
            logger.info(f"🗑️ Deleted file not in map (ignored): {file_path}")

    def on_modified(self, event):
        """Handle local file modification (and creation)."""
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        
        # map creation events are often handled here too by watchdog on some platforms,
        # but let's trust explicit methods. 
        # Actually on_created calls on_modified usually? No, they are separate.
        # But for 'created', we want similar logic to 'modified' (push).

        self.handle_file_change(event.src_path)

    def on_created(self, event):
        """Handle file creation."""
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        self.handle_file_change(event.src_path)

    def is_debounced(self, file_path: str) -> bool:
        """Check if file event should be ignored due to debounce."""
        last_time = self.recently_processed.get(file_path)
        if last_time and (datetime.now() - last_time).total_seconds() < self.DEBOUNCE_SECONDS:
            return True
        return False

    def handle_file_change(self, src_path_str):
        file_path = Path(src_path_str)
        if self.is_debounced(str(file_path)):
            return
        
        # Push to cloud
        success = self.push_to_cloud(file_path)
        if success:
            logger.info(f"☁️ Pushed to Cloud: {file_path.name}")

    def delete_cloud_task(self, task_id: str):
        """Delete (or complete) a task in TickTick."""
        # We can either delete or complete. Let's Delete for now per user pref.
        # API for delete: DELETE /task/{taskId} ? No, batch delete usually.
        # Let's try batch delete.
        try:
            payload = {
                "delete": [{"taskId": task_id, "projectId": "inbox1018769940"}] # TODO: dynamic project ID
            }
            resp = requests.post(
                f'{API_BASE}/batch/task',
                headers=self.headers,
                json=payload,
                timeout=10
            )
            if resp.status_code == 200:
                logger.info("✅ Cloud Deletion Successful")
            else:
                logger.error(f"❌ Cloud Delete Failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"❌ Cloud Delete Error: {e}")

    def update_task_title(self, task_id: str, new_title: str):
        """Update just the title of a task."""
        try:
            payload = {
                "update": [{"id": task_id, "title": new_title, "projectId": "inbox1018769940"}] 
            }
            requests.post(f'{API_BASE}/batch/task', headers=self.headers, json=payload)
            logger.info(f"✏️ Renamed Cloud Task: {new_title}")
        except Exception as e:
            logger.error(f"Rename failed: {e}")

    def push_to_cloud(self, file_path: Path) -> bool:
        """Push local file content to TickTick cloud via API."""
        time.sleep(0.2)  # Small delay for file write completion
        
        metadata, content = parse_frontmatter(file_path)
        task_id = metadata.get('task_id')
        project_id = metadata.get('project_id', 'inbox1018769940')
        
        if not task_id:
            return False
            
        # Update map
        self.path_map[str(file_path)] = task_id
        
        try:
            # Batch update API
            payload = {
                "update": [{
                    "id": task_id,
                    "projectId": project_id,
                    "content": content,
                    "title": metadata.get('title', file_path.stem) # Ensure title is synced
                }]
            }
            
            resp = requests.post(
                f'{API_BASE}/batch/task',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if not result.get('id2error', {}).get(task_id):
                    # Record debounce
                    self.recently_processed[str(file_path)] = datetime.now()
                    return True
                else:
                    logger.error(f"❌ API error: {result['id2error'][task_id]}")
            else:
                logger.error(f"❌ HTTP {resp.status_code}: {resp.text[:100]}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Push failed: {e}")
            return False

    def pull_from_cloud(self):
        """Pull updates from TickTick cloud."""
        try:
            # Get all tasks from inbox
            resp = requests.get(
                f'{API_BASE}/project/inbox1018769940/tasks',
                headers=self.headers,
                timeout=30
            )
            
            if resp.status_code != 200:
                logger.error(f"❌ Pull failed: HTTP {resp.status_code}")
                return
            
            tasks = resp.json()
            
            # --- Check for Remote Deletions ---
            # If we have a file in map, but it's NOT in the cloud list, 
            # and it wasn't just created (safety check), maybe we should delete local?
            # Issue: 'tasks' only contains INBOX tasks. If task moved to another project, it disappears here.
            # We shouldn't auto-delete local files just because they aren't in Inbox, 
            # unless we are sure they are deleted. 
            # For now, let's stick to Local->Cloud deletion only.
            
            for task in tasks:
                if task.get('kind') != 'NOTE':
                    continue
                self.sync_task_to_local(task)
                
        except Exception as e:
            logger.error(f"❌ Pull failed: {e}")

    def sync_task_to_local(self, task: dict):
        """Sync a single task from cloud to local file."""
        task_id = task.get('id')
        title = task.get('title', 'untitled')
        content = task.get('content', '')
        tags = task.get('tags', [])
        modified_time = task.get('modifiedTime', '')
        project_id = task.get('projectId', '')
        
        # Update Map Check
        # We might already have this task mapped to a path
        # But we need to search filesystem if map is empty (first run) or desync
        
        found_file = None
        
        # 1. Try Map First
        for path_str, map_id in list(self.path_map.items()):
            if map_id == task_id:
                if Path(path_str).exists():
                    found_file = Path(path_str)
                    break
                else:
                    # Stale map entry
                    del self.path_map[path_str]
        
        # 2. If not in map, search (fallback)
        if not found_file:
            for md_file in LOCAL_DOC_DIR.rglob('*.md'):
                if '.conflict' in md_file.name:
                    continue
                # Optimisation: Check map first to skip opening files we already know?
                # For now keep robust search
                meta, _ = parse_frontmatter(md_file)
                if meta.get('task_id') == task_id:
                    found_file = md_file
                    self.path_map[str(found_file)] = task_id # Update map
                    break
        
        # Handle new file
        if not found_file:
            func_level = extract_func_level(tags)
            folder_path = LOCAL_DOC_DIR / func_level
            folder_path.mkdir(exist_ok=True)
            
            safe_title = sanitize_filename(title)
            filename = f"{safe_title}.md"
            filepath = folder_path / filename
            
            counter = 1
            while filepath.exists():
                filename = f"{safe_title}_{counter}.md"
                filepath = folder_path / filename
                counter += 1
            
            logger.info(f"✨ New Note: {filename}")
            self.write_local_file(filepath, task_id, title, tags, modified_time, content, project_id)
            return
        
        # Check if cloud is newer
        local_meta, local_content = parse_frontmatter(found_file)
        local_mtime_str = local_meta.get('modified_time', '')
        
        # Convert Cloud UTC to Local Time
        cloud_dt = None
        if modified_time:
            try:
                # 2026-01-16T03:46:59.000+0000 -> parse
                # Simplest way: take first 19 chars, assume UTC, add 8 hours (for China) 
                # or use system timezone
                utc_dt = datetime.strptime(modified_time[:19], '%Y-%m-%dT%H:%M:%S')
                # Add local timezone offset (assuming sync is running on user's local machine)
                now = datetime.now()
                utcnow = datetime.utcnow()
                offset = now - utcnow
                local_dt = utc_dt + offset
                cloud_mtime_str = local_dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"Date parse error: {e}")
                cloud_mtime_str = modified_time
        else:
            cloud_mtime_str = ''
            
        # Content comparison
        if content and local_content:
            if content.strip() == local_content.strip():
                return  # No change
        
        # Compare strings (now both local time)
        if cloud_mtime_str > local_mtime_str:
            logger.info(f"⬇️ Pulling Update: {found_file.name}")
            # Pass CONVERTED local time to writer
            self.write_local_file(found_file, task_id, title, tags, cloud_mtime_str, content, project_id)

    def write_local_file(self, filepath, task_id, title, tags, modified_time, content, project_id):
        """Write content to local .md file with frontmatter."""
        # Record debounce BEFORE writing
        self.recently_processed[str(filepath)] = datetime.now()
        
        # Format tags for frontmatter
        tag_str = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else str(tags)
        
        # Use provided modified_time (should be local formatted string by now)
        mtime_str = modified_time if modified_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        file_content = f"""---
task_id: {task_id}
project_id: {project_id}
title: {title}
tag: {tag_str}
modified_time: {mtime_str}
---

{content}
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)


def run_daemon():
    """Main daemon entry point."""
    print("🚀 TickTick Sync Daemon (Cloud API Mode)")
    print(f"📂 Watching: {LOCAL_DOC_DIR}")
    print(f"☁️ API: {API_BASE}")
    print(f"⏱️ Polling every {POLL_INTERVAL}s")
    print("-" * 40)
    
    daemon = CloudSyncDaemon()
    observer = Observer()
    observer.schedule(daemon, str(LOCAL_DOC_DIR), recursive=True)
    observer.start()
    
    # Initial pull
    logger.info("🔄 Initial cloud sync...")
    daemon.pull_from_cloud()
    
    try:
        while True:
            time.sleep(POLL_INTERVAL)
            daemon.pull_from_cloud()
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Daemon stopped.")
    observer.join()


if __name__ == "__main__":
    run_daemon()
