# -*- coding: utf-8 -*-
"""
TickTick Pull Script v2
Extract task content from '收集箱' (Inbox) project to local .md files.
Organize by func_level_X tags into subfolders.
"""
import sys
import io
import re
import json

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import os
from pathlib import Path

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
    """
    Extract func_level tag from JSON tag string.
    Returns folder name like 'func_level_1' or 'no_tag' if not found.
    """
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


def pull_notes():
    """Extract all notes from '收集箱' to local .md files, organized by func_level."""
    
    if not TICKTICK_DB_PATH.exists():
        print(f"❌ Error: Database not found: {TICKTICK_DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(str(TICKTICK_DB_PATH))
        cursor = conn.cursor()
        
        # Get NOTES (not tasks) from 收集箱
        # kind = 'NOTE' for notes, 'TEXT' for regular tasks
        cursor.execute("""
            SELECT id, title, content, tag, modifiedTime
            FROM TaskModel
            WHERE projectId = 'inbox1018769940' 
              AND deleted = 0
              AND kind = 'NOTE'
            ORDER BY modifiedTime DESC
        """)
        
        tasks = cursor.fetchall()
        print(f"📝 Found {len(tasks)} tasks in 收集箱\n")
        
        if not tasks:
            print("⚠️ No tasks found.")
            conn.close()
            return False
        
        # Create output directory
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Count by folder
        folder_counts = {}
        exported = 0
        
        for task_id, title, content, tag, modified_time in tasks:
            # Skip tasks without meaningful content
            if not content or not content.strip():
                continue
            
            # Determine folder based on tag
            func_level = extract_func_level(tag)
            folder_path = OUTPUT_DIR / func_level
            folder_path.mkdir(exist_ok=True)
            
            # Track counts
            folder_counts[func_level] = folder_counts.get(func_level, 0) + 1
            
            # Generate safe filename
            safe_title = sanitize_filename(title) if title else 'untitled'
            filename = f"{safe_title}.md"
            filepath = folder_path / filename
            
            # Handle duplicate filenames
            counter = 1
            while filepath.exists():
                filename = f"{safe_title}_{counter}.md"
                filepath = folder_path / filename
                counter += 1
            
            # Build file content with frontmatter metadata
            file_content = f"""---
task_id: {task_id}
title: "{title}"
tag: {tag}
modified_time: {modified_time}
---

{content}
"""
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            print(f"✅ [{func_level}] {filename}")
            exported += 1
        
        conn.close()
        
        print(f"\n{'='*50}")
        print(f"✅ Successfully exported {exported} notes\n")
        print("📁 Folder breakdown:")
        for folder, count in sorted(folder_counts.items()):
            print(f"   {folder}: {count} files")
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
    print("TickTick Notes Export Tool (v2 - By Tag)")
    print("=" * 50)
    print()
    pull_notes()
