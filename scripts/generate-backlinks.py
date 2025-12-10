#!/usr/bin/env python3
"""
Generate backlink data for GWiki notes.

Scans all \wref links and computes which notes link to which.
Saves to .gwiki-metadata.json for use by index generator.

Usage:
  python3 generate-backlinks.py
"""

import re
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
NOTES_DIR = ROOT / "notes"
METADATA_FILE = ROOT / ".gwiki-metadata.json"


def extract_wref_links(tex_file: Path):
    """Extract all \wref{target} links from a file."""
    try:
        content = tex_file.read_text(encoding='utf-8')
    except Exception:
        return []

    targets = []
    lines = content.splitlines()

    for line in lines:
        # Skip comments
        if re.match(r'^\s*%', line):
            continue

        # Find all \wref{target} patterns
        for match in re.finditer(r'\\wref\{([^}]+)\}', line):
            target = match.group(1)

            # Strip section references
            if '#' in target:
                target = target.split('#')[0]

            # Skip internal references
            if target.startswith('#'):
                continue

            targets.append(target.strip())

    return targets


def generate_backlinks():
    """Generate backlink graph."""
    # Forward links: note -> [targets it links to]
    forward_links = {}

    # Backward links: note -> [notes that link to it]
    backlinks = defaultdict(list)

    # Scan all notes
    for tex_file in sorted(NOTES_DIR.glob("*.tex")):
        note_name = tex_file.stem
        targets = extract_wref_links(tex_file)

        forward_links[note_name] = targets

        # Build backlinks
        for target in targets:
            if target != note_name:  # Skip self-links
                backlinks[target].append(note_name)

    # Remove duplicates and sort
    backlinks = {
        target: sorted(set(sources))
        for target, sources in backlinks.items()
    }

    return forward_links, dict(backlinks)


def save_backlinks(forward_links, backlinks):
    """Save backlink data to metadata file."""
    # Load existing metadata
    if METADATA_FILE.exists():
        try:
            metadata = json.loads(METADATA_FILE.read_text())
        except:
            metadata = {}
    else:
        metadata = {}

    # Update with new link data
    metadata['forward_links'] = forward_links
    metadata['backlinks'] = backlinks

    # Save
    METADATA_FILE.write_text(json.dumps(metadata, indent=2, sort_keys=True))


def main():
    """Generate and save backlinks."""
    print("Generating backlinks...")

    forward_links, backlinks = generate_backlinks()

    total_links = sum(len(targets) for targets in forward_links.values())
    notes_with_backlinks = len([n for n in backlinks if backlinks[n]])

    save_backlinks(forward_links, backlinks)

    print(f"✓ Generated backlinks")
    print(f"  - {total_links} forward links")
    print(f"  - {notes_with_backlinks} notes have incoming links")


if __name__ == "__main__":
    main()
