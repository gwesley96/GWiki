#!/usr/bin/env python3
"""
Convert LaTeX delimiters \[ \] and \( \) to Dollar signs $$ and $ in Markdown files.
"""

import sys
import os
import re
from pathlib import Path

VAULT_DIR = Path("/Users/greysonwesley/Desktop/workflow/wiki")

def fix_delimiters(content):
    # display math \[ ... \] -> $$ ... $$
    # We use re.sub with care.
    # Non-greedy match for content? 
    # Actually, simplistic replacement of literals is safer if balanced?
    # No, \[ is distinct start.
    
    # Replace \[ with $$
    content = content.replace(r'\[', '$$')
    content = content.replace(r'\]', '$$')
    
    # Replace \( with $
    content = content.replace(r'\(', '$')
    content = content.replace(r'\)', '$')
    
    return content

def process_file(path, dry_run=False):
    try:
        old_content = path.read_text(encoding='utf-8')
        new_content = fix_delimiters(old_content)
        
        if old_content != new_content:
            if dry_run:
                print(f"[Dry Run] Would update {path.name}")
            else:
                path.write_text(new_content, encoding='utf-8')
                print(f"Updated {path.name}")
            return True
    except Exception as e:
        print(f"Error processing {path}: {e}")
    return False

def main():
    if not VAULT_DIR.exists():
        print(f"Error: Vault not found at {VAULT_DIR}")
        sys.exit(1)
        
    dry_run = '--dry-run' in sys.argv
    
    count = 0
    for md_file in VAULT_DIR.glob("*.md"):
        if process_file(md_file, dry_run):
            count += 1
            
    if dry_run:
        print(f"Dry run complete. Would update {count} files.")
    else:
        print(f"Fixed delimiters in {count} files.")

if __name__ == "__main__":
    main()
