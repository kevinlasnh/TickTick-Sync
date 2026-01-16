# -*- coding: utf-8 -*-
"""
TickTick Push Script v3 - Incremental Sync
Only pushes files that have been modified locally (file mtime > frontmatter modified_time).
Automatically closes and reopens TickTick.
"""
import sys
import io
import re
import shutil
import subprocess
import time

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Configuration
TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'
TICKTICK_EXE_PATH = Path(os.environ['LOCALAPPDATA']) / 'TickTick' / 'TickTick.exe'
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = Path(r'C:\Zero\Doc\Local\Life\Personal_dataBase')
BACKUP_DIR = SCRIPT_DIR / 'backups'


def close_ticktick():
    """Close TickTick application if running."""
    print("🔄 Closing TickTick...")
    result = subprocess.run(
        ['taskkill', '/f', '/im', 'TickTick.exe'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ TickTick closed")
        time.sleep(1)
        return True
    elif 'not found' in result.stderr.lower() or result.returncode == 128:
        print("ℹ️ TickTick was not running")
        return True
    else:
        print(f"⚠️ Could not close TickTick: {result.stderr}")
        return True


def open_ticktick():
    """Open TickTick application."""
    print("🚀 Opening TickTick...")
    if TICKTICK_EXE_PATH.exists():
        subprocess.Popen([str(TICKTICK_EXE_PATH)], shell=True)
        print("✅ TickTick started")
    else:
        subprocess.Popen('start TickTick:', shell=True)
        print("✅ TickTick started (via protocol)")


def backup_database():
    """Backup database before modification."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'TickTick_backup_{timestamp}.db'
    shutil.copy2(TICKTICK_DB_PATH, backup_path)
    print(f"📦 Database backed up: {backup_path.name}")
    return backup_path


def parse_frontmatter(file_path: Path) -> tuple[dict, str]:
    """Parse frontmatter and content from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
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


def parse_datetime(dt_str: str) -> datetime | None:
    """Parse datetime string from various formats."""
    if not dt_str:
        return None
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def is_locally_modified(file_path: Path, frontmatter_mtime: str) -> bool:
    """Check if local file was modified after the frontmatter timestamp."""
    # Get file modification time
    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    
    # Parse frontmatter modified_time
    fm_mtime = parse_datetime(frontmatter_mtime)
    
    if not fm_mtime:
        # No frontmatter time, assume modified
        return True
    
    # Add 1 second buffer to handle filesystem precision
    return file_mtime > fm_mtime


def push_notes():
    """Push only locally modified notes to TickTick database."""
    
    if not TICKTICK_DB_PATH.exists():
        print(f"❌ Error: Database not found: {TICKTICK_DB_PATH}")
        return False
    
    if not INPUT_DIR.exists():
        print(f"❌ Error: Note folder not found: {INPUT_DIR}")
        print("Run pull.py first to export notes.")
        return False
    
    md_files = list(INPUT_DIR.rglob('*.md'))
    if not md_files:
        print("⚠️ No .md files found.")
        return False
    
    # First pass: identify modified files
    modified_files = []
    for md_file in md_files:
        metadata, content = parse_frontmatter(md_file)
        task_id = metadata.get('task_id')
        if not task_id:
            continue
        
        fm_mtime = metadata.get('modified_time', '')
        if is_locally_modified(md_file, fm_mtime):
            modified_files.append((md_file, metadata, content))
    
    if not modified_files:
        print("ℹ️ No locally modified files to push.")
        return True
    
    print(f"📝 Found {len(modified_files)} locally modified files\n")
    
    # Backup before modification
    backup_database()
    print()
    
    try:
        conn = sqlite3.connect(str(TICKTICK_DB_PATH))
        cursor = conn.cursor()
        
        updated = 0
        skipped = 0
        errors = 0
        
        for md_file, metadata, content in modified_files:
            task_id = metadata.get('task_id')
            
            # Check if task exists
            cursor.execute("SELECT id, title FROM TaskModel WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                print(f"⚠️ Task not found in DB: {task_id}")
                skipped += 1
                continue
            
            db_title = row[1]
            new_mtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute("""
                    UPDATE TaskModel 
                    SET content = ?, modifiedTime = ?
                    WHERE id = ?
                """, (content, new_mtime, task_id))
                
                print(f"✅ Updated: {db_title}")
                updated += 1
                
            except sqlite3.Error as e:
                print(f"❌ Failed: {db_title}: {e}")
                errors += 1
        
        conn.commit()
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        
        print(f"\n{'='*50}")
        print(f"✅ Pushed: {updated} notes")
        if skipped:
            print(f"⏭️ Skipped: {skipped}")
        if errors:
            print(f"❌ Errors: {errors}")
        return True
        
    except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
            print("❌ Error: Database is locked!")
            print("Failed to close TickTick properly.")
        else:
            print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unknown error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("TickTick Notes Push (v3 - Incremental)")
    print("=" * 50)
    print()
    
    confirm = input("Push local changes to TickTick? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    print()
    close_ticktick()
    print()
    
    success = push_notes()
    print()
    
    if success:
        open_ticktick()
        print("\n🎉 Done!")
