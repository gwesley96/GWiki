
import os
import sys
import re
import subprocess
from pathlib import Path

# Paths
GWIKI_ROOT = Path("/Users/greysonwesley/Desktop/GWiki")
NOTES_DIR = GWIKI_ROOT / "notes"
VAULT_DIR = Path("/Users/greysonwesley/Desktop/workflow/wiki")
IMPORT_SCRIPT = GWIKI_ROOT / "scripts" / "import-from-obsidian.py"

def find_stubs():
    stubs = []
    print("Finding stubs...")
    for f in NOTES_DIR.glob("*.tex"):
        try:
            content = f.read_text(encoding='utf-8')
            if "This note is a placeholder for future content" in content:
                stubs.append(f.stem)
        except:
            pass
    print(f"Found {len(stubs)} stubs.")
    return stubs

def find_source_files(stubs):
    print("Indexing vault...")
    # Map stem -> full path
    sources = {}
    for f in VAULT_DIR.rglob("*.md"):
        sources[f.stem] = f
    
    matches = []
    for stub in stubs:
        if stub in sources:
            matches.append(sources[stub])
        else:
            print(f"Warning: No source found for stub '{stub}'")
            
    return matches

def main():
    stubs = find_stubs()
    if not stubs:
        print("No stubs found.")
        return

    sources = find_source_files(stubs)
    print(f"Found {len(sources)} matching source files.")
    
    # Import
    for src in sources:
        # We need to pass the RELATIVE path from the vault root to import-from-obsidian.py
        # because it joins it with OBSIDIAN_VAULT path.
        rel_path = src.relative_to(VAULT_DIR)
        print(f"Importing {rel_path}...")
        subprocess.run(["python3", str(IMPORT_SCRIPT), str(rel_path)], cwd=GWIKI_ROOT)

if __name__ == "__main__":
    main()
