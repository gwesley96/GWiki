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

def normalize_for_match(text: str) -> str:
    """Lowercase and strip separators/punctuation for matching."""
    return re.sub(r'[^a-z0-9]+', '', text.lower())

def ensure_list(value):
    """Normalize metadata fields to a list of strings."""
    if not value:
        return []
    if isinstance(value, list):
        return [v.strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(',') if v.strip()]

def slugify(text: str) -> str:
    """Produce a dash-separated, editor-friendly slug."""
    cleaned = re.sub(r'[–—]', '-', text)  # normalize en/em dash to hyphen
    cleaned = re.sub(r'[^a-zA-Z0-9\s_-]+', '', cleaned)
    cleaned = re.sub(r'[\s_]+', '-', cleaned.strip())
    cleaned = re.sub(r'-+', '-', cleaned)
    return cleaned.lower()

def parse_frontmatter(content: str) -> dict:
    """Parse YAML-style frontmatter from the top of a .tex file (commented with %)."""
    pattern = re.compile(r'^\s*%?\s*---\s*\n(.*?)\n\s*%?\s*---', re.DOTALL | re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return {}

    raw_block = match.group(1)
    lines = []
    for line in raw_block.splitlines():
        # Strip leading % and whitespace
        cleaned = re.sub(r'^\s*%+\s?', '', line)
        lines.append(cleaned)

    data = {}
    current_key = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if ':' in stripped and not stripped.startswith('-'):
            key, value = stripped.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            if value:
                if value.startswith('[') and value.endswith(']'):
                    data[key] = [v.strip() for v in value[1:-1].split(',') if v.strip()]
                else:
                    data[key] = value
            else:
                data[key] = []
            current_key = key
            continue

        if stripped.startswith('-') and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                item = stripped.lstrip('-').strip()
                if item:
                    data[current_key].append(item)

    return data

def extract_title_from_text(content: str):
    """Extract title using common macros."""
    match = re.search(r'\\Title\{([^}]+)\}', content)
    if match:
        return match.group(1)
    match = re.search(r'\\title\{([^}]+)\}', content)
    if match:
        return match.group(1)
    match = re.search(r'\\GWikiMeta\{[^}]*\}\{([^}]+)\}', content)
    if match:
        return match.group(1)
    return None

def extract_note_metadata(tex_file: Path):
    """Read a tex file once and extract title, tags, aliases, and mtime."""
    meta = {
        "name": tex_file.stem,
        "title": None,
        "path": str(tex_file.relative_to(ROOT)),
        "mtime": tex_file.stat().st_mtime,
        "tags": [],
        "aliases": [],
    }

    try:
        content = tex_file.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return meta

    frontmatter = parse_frontmatter(content)
    if frontmatter:
        meta["title"] = frontmatter.get("title") or meta["title"]
        meta["tags"] = ensure_list(
            frontmatter.get("tags") or frontmatter.get("tag")
        ) or meta["tags"]
        meta["aliases"] = ensure_list(
            frontmatter.get("aliases") or frontmatter.get("alias")
        ) or meta["aliases"]

    gwiki_meta = re.search(
        r'\\GWikiMeta\{[^}]*\}\{([^}]+)\}\{[^}]+\}(?:\[([^\]]*)\])?(?:\[([^\]]*)\])?',
        content
    )
    if gwiki_meta:
        if not meta["title"]:
            meta["title"] = gwiki_meta.group(1)
        if not meta["tags"] and gwiki_meta.group(2):
            meta["tags"] = ensure_list(gwiki_meta.group(2))
        if not meta["aliases"] and gwiki_meta.group(3):
            meta["aliases"] = ensure_list(gwiki_meta.group(3))

    if not meta["title"]:
        meta["title"] = extract_title_from_text(content) or meta["name"]

    if not meta["tags"]:
        tag_matches = re.findall(r'\\Tags\{([^}]*)\}', content)
        tags = []
        for tm in tag_matches:
            tags.extend(ensure_list(tm))
        meta["tags"] = tags

    if not meta["aliases"]:
        alias_match = re.search(r'\\Aliases\{([^}]*)\}', content)
        if alias_match:
            meta["aliases"] = ensure_list(alias_match.group(1))

    return meta

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
            completions.append(extract_note_metadata(tex_file))

    # Sort by modification time (most recent first)
    completions.sort(key=lambda x: x["mtime"], reverse=True)

    return completions

def generate_vscode_snippets(completions):
    """Generate VS Code snippets for \wref completion."""
    snippets = {}

    for i, item in enumerate(completions):
        name = item["name"]
        title = item["title"] or name

        # Keep prefixes scoped to \wref{...} so they only appear in the right context
        raw_prefixes = [
            f"\\wref{{{name}",
            f"\\wref{{{title}}}",
            "\\wref{",
        ]
        prefixes = []
        seen = set()
        for p in raw_prefixes:
            if p and p not in seen:
                prefixes.append(p)
                seen.add(p)

        # Create snippet that inserts \wref{name}[Title]
        snippets[f"wref-{name}"] = {
            "prefix": prefixes,
            "body": f"\\\\wref{{{name}}}[${{1:{title}}}]$0",
            "description": f"{title} ({item['path']})"
        }

        # Alias snippets add the display text automatically
        for idx, alias in enumerate(item.get("aliases", [])):
            alias_prefixes = [
                f"\\wref{{{alias}}}",
                "\\wref{",
            ]
            snippets[f"wref-{name}-alias-{idx}"] = {
                "prefix": alias_prefixes,
                "body": f"\\\\wref{{{name}}}[{alias}]$0",
                "description": f"{title} (alias: {alias}) ({item['path']})"
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
                "filterText": " ".join(dict.fromkeys([
                    item["name"],
                    slugify(item["name"]),
                    normalize_for_match(item["name"]),
                    slugify(item["title"] or item["name"]),
                    normalize_for_match(item["title"] or item["name"]),
                    *[slugify(a) for a in item.get("aliases", [])],
                    *[normalize_for_match(a) for a in item.get("aliases", [])],
                ])),
                "aliases": item.get("aliases", []),
                "tags": item.get("tags", []),
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
