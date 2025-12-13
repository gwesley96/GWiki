#!/usr/bin/env python3
import sys
import re
import json
import os
from pathlib import Path
from datetime import datetime

# Logic to extract creation date, matching tex-to-html.py behavior

def get_creation_date(note_name):
    # 1. Try to read from Markdown file frontmatter (Source of Truth)
    # Recursively search for the .md file in the wiki directory
    # Adjust this path if necessary, assuming script runs from repo root
    
    # We assume this script is run from repo root or scripts dir?
    # Let's try to find repo root relative to this script
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    wiki_root = Path("/Users/greysonwesley/Desktop/workflow/wiki")
    if not wiki_root.exists():
        # Fallback to relative if absolute path fails?
        pass

    found = list(wiki_root.rglob(f"{note_name}.md"))
    if found:
        md_path = found[0]
        try:
            content = md_path.read_text(encoding='utf-8')
            match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                fm = match.group(1)
                # Prioritize 'date created'
                date_match = re.search(r'^date created:\s*(.+)$', fm, re.MULTILINE | re.IGNORECASE)
                if not date_match:
                    date_match = re.search(r'^date:\s*(.+)$', fm, re.MULTILINE | re.IGNORECASE)
                
                if date_match:
                    raw_full = date_match.group(1).strip()
                    # Clean up
                    raw = re.sub(r'\s+[A-Z]{2,3}$', '', raw_full) # Remove timezone suffix
                    raw = raw.replace(' at ', ' ')
                    if 'am' in raw: raw = raw.replace('am', 'AM')
                    if 'pm' in raw: raw = raw.replace('pm', 'PM')
                    
                    formats = [
                        '%B %d, %Y %I:%M %p', # August 17, 2025 10:09 PM
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M',
                        '%Y-%m-%d',
                        '%B %d, %Y %H:%M'
                    ]
                    
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(raw, fmt)
                            # Return in a format usable by LaTeX or just the standard display format?
                            # The user wants "correct way... like the html".
                            # HTML uses: %B %d, %Y at %l:%M %p ET
                            return dt.strftime('%B %d, %Y at %l:%M %p ET')
                        except ValueError:
                            continue
        except Exception as e:
            # print(f"Error reading MD: {e}", file=sys.stderr)
            pass

    # 2. Fallback to .gwiki-metadata.json
    try:
        meta_path = repo_root / '.gwiki-metadata.json'
        if meta_path.exists():
            data = json.loads(meta_path.read_text())
            date_str = data.get('creation_dates', {}).get(note_name)
            if date_str:
                # Metadata usually YYYY-MM-DD
                # Convert to nice format if possible
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    return dt.strftime('%B %d, %Y')
                except:
                    return date_str
    except:
        pass

    return ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: get-date.py <note_name>")
        sys.exit(1)
    
    note_name = sys.argv[1]
    # Strip extension if provided
    if note_name.endswith('.tex'):
        note_name = note_name[:-4]
        
    date = get_creation_date(note_name)
    print(date)
