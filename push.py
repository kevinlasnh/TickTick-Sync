# -*- coding: utf-8 -*-
"""
TickTick Push Script
Write local .md file changes back to TickTick database.
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
        time.sleep(1)  # Wait for process to fully terminate
        return True
    elif 'not found' in result.stderr.lower() or result.returncode == 128:
        print("ℹ️ TickTick was not running")
        return True
    else:
        print(f"⚠️ Could not close TickTick: {result.stderr}")
        return True  # Continue anyway


def open_ticktick():
    """Open TickTick application."""
    print("🚀 Opening TickTick...")
    if TICKTICK_EXE_PATH.exists():
        subprocess.Popen([str(TICKTICK_EXE_PATH)], shell=True)
        print("✅ TickTick started")
    else:
        # Try alternative path or shell start
        subprocess.Popen('start TickTick:', shell=True)
        print("✅ TickTick started (via protocol)")


def get_current_mtime() -> int:
    """Get current timestamp in milliseconds (for TickTick sync)."""
    return int(datetime.now().timestamp() * 1000)


def backup_database():
    """Backup the database before modification."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'TickTick_backup_{timestamp}.db'
    shutil.copy2(TICKTICK_DB_PATH, backup_path)
    print(f"📦 Database backed up: {backup_path.name}")
    return backup_path


def parse_frontmatter(file_path: Path) -> tuple[dict, str]:
    """
    Parse YAML frontmatter and content from a markdown file.
    Returns (metadata_dict, content_string).
    Uses simple regex parsing to avoid yaml dependency.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Check for YAML frontmatter
    if not text.startswith('---'):
        return {}, text
    
    # Find the closing ---
    end_idx = text.find('---', 3)
    if end_idx == -1:
        return {}, text
    
    frontmatter_str = text[3:end_idx].strip()
    content = text[end_idx + 3:].strip()
    
    # Simple regex-based parsing for key: value pairs
    metadata = {}
    for line in frontmatter_str.split('\n'):
        match = re.match(r'^(\w+):\s*(.+)$', line.strip())
        if match:
            key, value = match.groups()
            # Remove surrounding quotes if present
            value = value.strip().strip('"').strip("'")
            metadata[key] = value
    
    return metadata, content


def push_notes():
    """Push local .md changes back to TickTick database."""
    
    if not TICKTICK_DB_PATH.exists():
        print(f"❌ Error: Database not found: {TICKTICK_DB_PATH}")
        return False
    
    if not INPUT_DIR.exists():
        print(f"❌ Error: Note folder not found: {INPUT_DIR}")
        print("Run pull.py first to export notes.")
        return False
    
    # Collect all .md files from subdirectories
    md_files = list(INPUT_DIR.rglob('*.md'))
    if not md_files:
        print("⚠️ No .md files found to push.")
        return False
    
    print(f"📝 Found {len(md_files)} .md files to process\n")
    
    # Backup database before modification
    backup_database()
    print()
    
    try:
        conn = sqlite3.connect(str(TICKTICK_DB_PATH))
        cursor = conn.cursor()
        
        updated = 0
        skipped = 0
        errors = 0
        
        for md_file in md_files:
            metadata, content = parse_frontmatter(md_file)
            
            task_id = metadata.get('task_id')
            if not task_id:
                print(f"⚠️ Skipping (no task_id): {md_file.name}")
                skipped += 1
                continue
            
            # Check if task exists in DB
            cursor.execute("SELECT id, title FROM TaskModel WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                print(f"⚠️ Task not found in DB: {task_id} ({md_file.name})")
                skipped += 1
                continue
            
            db_title = row[1]
            
            # Update content and modifiedTime
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
                print(f"❌ Failed to update {db_title}: {e}")
                errors += 1
        
        # Commit all changes
        conn.commit()
        
        # Force WAL checkpoint to ensure persistence
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        conn.close()
        
        print(f"\n{'='*50}")
        print(f"✅ Successfully updated: {updated} notes")
        if skipped:
            print(f"⏭️ Skipped: {skipped}")
        if errors:
            print(f"❌ Errors: {errors}")
        return True
        
    except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
            print("❌ Error: Database is locked!")
            print("Failed to close TickTick properly. Please close it manually and retry.")
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
    print("TickTick Notes Push Tool")
    print("=" * 50)
    print()
    
    confirm = input("Push changes to TickTick? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    print()
    
    # Step 1: Close TickTick
    close_ticktick()
    print()
    
    # Step 2: Push notes
    success = push_notes()
    print()
    
    # Step 3: Reopen TickTick
    if success:
        open_ticktick()
        print("\n🎉 Done! TickTick will sync changes to cloud.")
