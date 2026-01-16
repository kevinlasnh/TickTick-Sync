# -*- coding: utf-8 -*-
"""
TickTick Pull Script v4 - Incremental Sync with Conflict Detection
Only updates local files when cloud version is newer.
Detects and handles conflicts when both sides have changes.
"""
import sys
import io
import re
import json
import shutil

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Configuration
TICKTICK_DB_PATH = Path(os.environ['APPDATA']) / 'Tick_Tick' / 'TickTick.db'
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = Path(r'C:\Zero\Doc\Local\Life\Personal_dataBase')


def sanitize_filename(name: str) -> str:
    """Remove characters that are not allowed in filenames."""
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)
    sanitized = sanitized.strip(' .')
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized or 'untitled'


def extract_func_level(tag_str: str) -> str:
    """Extract func_level tag from JSON tag string."""
    if not tag_str:
        return 'no_tag'
    try:
        tags = json.loads(tag_str)
        for tag in tags:
            if tag.startswith('func_level_'):
                return tag
        return 'no_tag'
    except json.JSONDecodeError:
        return 'no_tag'


def parse_frontmatter(file_path: Path) -> tuple[dict, str]:
    """Parse frontmatter and content from existing local file."""
    if not file_path.exists():
        return {}, ""
    
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


def find_existing_file(task_id: str) -> Path | None:
    """Find existing local file by task_id in frontmatter."""
    for md_file in OUTPUT_DIR.rglob('*.md'):
        if '.conflict' in md_file.name:
            continue
        metadata, _ = parse_frontmatter(md_file)
        if metadata.get('task_id') == task_id:
            return md_file
    return None


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
    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    fm_mtime = parse_datetime(frontmatter_mtime)
    if not fm_mtime:
        return True
    # Add 2 second buffer for filesystem precision
    from datetime import timedelta
    return file_mtime > (fm_mtime + timedelta(seconds=2))


def pull_notes():
    """Pull notes with incremental sync and conflict detection."""
    
    if not TICKTICK_DB_PATH.exists():
        print(f"❌ Error: Database not found: {TICKTICK_DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(str(TICKTICK_DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, tag, modifiedTime
            FROM TaskModel
            WHERE projectId = 'inbox1018769940' 
              AND deleted = 0
              AND kind = 'NOTE'
            ORDER BY modifiedTime DESC
        """)
        
        tasks = cursor.fetchall()
        print(f"📝 Found {len(tasks)} notes in 收集箱\n")
        
        if not tasks:
            print("⚠️ No notes found.")
            conn.close()
            return False
        
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        updated = 0
        skipped = 0
        new_files = 0
        conflicts = 0
        
        for task_id, title, content, tag, modified_time in tasks:
            if not content or not content.strip():
                continue
            
            existing_file = find_existing_file(task_id)
            
            if existing_file:
                local_meta, local_content = parse_frontmatter(existing_file)
                local_fm_mtime = parse_datetime(local_meta.get('modified_time', ''))
                cloud_mtime = parse_datetime(modified_time) if modified_time else None
                
                # Check if local file was edited by user
                local_edited = is_locally_modified(existing_file, local_meta.get('modified_time', ''))
                
                # Check if cloud has newer version
                cloud_newer = cloud_mtime and local_fm_mtime and cloud_mtime > local_fm_mtime
                
                if local_edited and cloud_newer:
                    # CONFLICT: Both sides modified!
                    print(f"⚠️ CONFLICT: {title}")
                    print(f"   → Local edited + Cloud updated")
                    
                    # Save local version as .conflict.md
                    conflict_file = existing_file.with_suffix('.conflict.md')
                    shutil.copy2(existing_file, conflict_file)
                    print(f"   → Local backup: {conflict_file.name}")
                    
                    # Pull cloud version
                    filepath = existing_file
                    conflicts += 1
                    
                elif cloud_newer:
                    # Cloud is newer, local not edited - safe to update
                    print(f"🔄 Updated (cloud newer): {title}")
                    filepath = existing_file
                    updated += 1
                    
                elif local_edited:
                    # Local edited, cloud not newer - skip (will push later)
                    print(f"⏭️ Skipped (local edited, pending push): {title}")
                    skipped += 1
                    continue
                    
                else:
                    # No changes on either side
                    print(f"⏭️ Skipped (no changes): {title}")
                    skipped += 1
                    continue
            else:
                # New file
                func_level = extract_func_level(tag)
                folder_path = OUTPUT_DIR / func_level
                folder_path.mkdir(exist_ok=True)
                
                safe_title = sanitize_filename(title) if title else 'untitled'
                filename = f"{safe_title}.md"
                filepath = folder_path / filename
                
                counter = 1
                while filepath.exists():
                    filename = f"{safe_title}_{counter}.md"
                    filepath = folder_path / filename
                    counter += 1
                
                print(f"✅ New: [{func_level}] {filename}")
                new_files += 1
            
            # Write file
            file_content = f"""---
task_id: {task_id}
title: "{title}"
tag: {tag}
modified_time: {modified_time}
---

{content}
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Set file mtime to match cloud modified_time
            cloud_mtime = parse_datetime(modified_time)
            if cloud_mtime:
                mtime_timestamp = cloud_mtime.timestamp()
                os.utime(filepath, (mtime_timestamp, mtime_timestamp))
        
        conn.close()
        
        print(f"\n{'='*50}")
        print(f"✅ New files: {new_files}")
        print(f"🔄 Updated (cloud newer): {updated}")
        print(f"⏭️ Skipped: {skipped}")
        if conflicts:
            print(f"⚠️ CONFLICTS: {conflicts}")
            print(f"\n📌 Please manually merge .conflict.md files!")
        print(f"\n📂 Output: {OUTPUT_DIR}")
        return True
        
    except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
            print("❌ Error: Database is locked!")
            print("Please CLOSE TickTick completely, then retry.")
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
    print("TickTick Notes Pull (v4 - Conflict Detection)")
    print("=" * 50)
    print()
    pull_notes()
