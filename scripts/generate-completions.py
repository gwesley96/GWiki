#!/usr/bin/env python3
"""
GWiki Completion Generator

Generates VS Code completion data for \wref{} autocomplete.
Run this after adding/renaming files, or use watch mode.

Usage:
  python3 generate-completions.py          # Generate once
  python3 generate-completions.py --watch  # Watch and regenerate
"""

import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
NOTES_DIR = ROOT / "notes"  # All notes in one place now
ARTICLES_DIR = ROOT / "articles"  # Legacy support
WIKI_DIR = ROOT / "wiki"  # Legacy support
VSCODE_DIR = ROOT / ".vscode"
OUTPUT = VSCODE_DIR / "gwiki-completions.json"

def get_title_from_tex(filepath):
    """Extract title from a .tex file."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        # Try \Title{...}
        match = re.search(r'\\Title\{([^}]+)\}', content)
        if match:
            return match.group(1)
        # Try \title{...}
        match = re.search(r'\\title\{([^}]+)\}', content)
        if match:
            return match.group(1)
        # Try \GWikiMeta{...}{title}{...}
        match = re.search(r'\\GWikiMeta\{[^}]*\}\{([^}]+)\}', content)
        if match:
            return match.group(1)
    except:
        pass
    return None

def scan_notes():
    """Scan all .tex files and return completion data."""
    completions = []

    # Scan all possible directories
    dirs_to_scan = []
    if NOTES_DIR.exists():
        dirs_to_scan.append(NOTES_DIR)
    if ARTICLES_DIR.exists():
        dirs_to_scan.append(ARTICLES_DIR)
    if WIKI_DIR.exists():
        dirs_to_scan.append(WIKI_DIR)

    for directory in dirs_to_scan:
        for tex_file in directory.glob("*.tex"):
            name = tex_file.stem  # filename without .tex
            title = get_title_from_tex(tex_file) or name
            mtime = tex_file.stat().st_mtime

            completions.append({
                "name": name,
                "title": title,
                "path": str(tex_file.relative_to(ROOT)),
                "mtime": mtime,
            })

    # Sort by modification time (most recent first)
    completions.sort(key=lambda x: x["mtime"], reverse=True)

    return completions

def generate_vscode_snippets(completions):
    """Generate VS Code snippets for \wref completion."""
    snippets = {}

    for i, item in enumerate(completions):
        name = item["name"]
        title = item["title"]

        # Create snippet that inserts \wref{name}[Title]
        snippets[f"wref-{name}"] = {
            "prefix": [f"wref{name}", name, title.lower() if title else name],
            "body": f"\\\\wref{{{name}}}[${{1:{title}}}]$0",
            "description": f"{title} ({item['path']})"
        }

    return snippets

def generate_completion_data(completions):
    """Generate completion data file for the extension."""
    return {
        "generated": datetime.now().isoformat(),
        "count": len(completions),
        "completions": [
            {
                "label": item["title"] or item["name"],
                "insertText": item["name"],
                "detail": item["path"],
                "sortText": f"{i:04d}",  # Sort by recency
            }
            for i, item in enumerate(completions)
        ]
    }

def main():
    VSCODE_DIR.mkdir(exist_ok=True)

    completions = scan_notes()

    # Generate completion data
    data = generate_completion_data(completions)
    OUTPUT.write_text(json.dumps(data, indent=2))
    print(f"Generated {len(completions)} completions -> {OUTPUT}")

    # Generate snippets
    snippets = generate_vscode_snippets(completions)
    snippets_file = VSCODE_DIR / "gwiki.code-snippets"
    snippets_file.write_text(json.dumps(snippets, indent=2))
    print(f"Generated snippets -> {snippets_file}")

    # Watch mode
    if "--watch" in sys.argv:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class Handler(FileSystemEventHandler):
                def on_any_event(self, event):
                    if event.src_path.endswith('.tex'):
                        print(f"\nFile changed: {event.src_path}")
                        main_generate()

            def main_generate():
                completions = scan_notes()
                data = generate_completion_data(completions)
                OUTPUT.write_text(json.dumps(data, indent=2))
                snippets = generate_vscode_snippets(completions)
                (VSCODE_DIR / "gwiki.code-snippets").write_text(json.dumps(snippets, indent=2))
                print(f"Regenerated {len(completions)} completions")

            observer = Observer()
            for d in [NOTES_DIR, ARTICLES_DIR, WIKI_DIR]:
                if d.exists():
                    observer.schedule(Handler(), str(d), recursive=False)

            observer.start()
            print("\nWatching for changes... (Ctrl+C to stop)")

            import time
            while True:
                time.sleep(1)

        except ImportError:
            print("\nWatch mode requires watchdog: pip install watchdog")
        except KeyboardInterrupt:
            print("\nStopped watching.")

if __name__ == "__main__":
    main()
