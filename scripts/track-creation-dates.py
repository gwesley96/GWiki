#!/usr/bin/env python3
"""
Track creation dates for GWiki notes.

Maintains a .gwiki-metadata.json file with creation timestamps.
When a new note appears, record its creation time.
Never overwrites existing creation dates.

Usage:
  python3 track-creation-dates.py
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
NOTES_DIR = ROOT / "notes"
METADATA_FILE = ROOT / ".gwiki-metadata.json"


def load_metadata():
    """Load existing metadata or return empty dict."""
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text())
        except:
            return {}
    return {}


def save_metadata(data):
    """Save metadata to disk."""
    METADATA_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))


def track_creation_dates():
    """Scan notes and record creation dates for new files."""
    metadata = load_metadata()

    if 'creation_dates' not in metadata:
        metadata['creation_dates'] = {}

    creation_dates = metadata['creation_dates']
    new_count = 0

    for tex_file in NOTES_DIR.glob("*.tex"):
        note_name = tex_file.stem

        # Skip if we already have a creation date
        if note_name in creation_dates:
            continue

        # Record creation date from file system
        stat = tex_file.stat()
        # Use birth time if available (macOS), else modification time
        created = getattr(stat, 'st_birthtime', stat.st_mtime)
        creation_dates[note_name] = datetime.fromtimestamp(created).strftime('%Y-%m-%d')
        new_count += 1

    if new_count > 0:
        save_metadata(metadata)
        print(f"Tracked {new_count} new note(s)")

    return metadata


if __name__ == "__main__":
    track_creation_dates()
