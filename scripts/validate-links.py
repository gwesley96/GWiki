#!/usr/bin/env python3
"""
Validate all \wref links in GWiki notes.

Checks that all \wref{target} references point to existing notes.
Reports broken links with source file and line number.

Usage:
  python3 validate-links.py           # Check all links
  python3 validate-links.py --strict  # Exit with error code if broken links found
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
NOTES_DIR = ROOT / "notes"

STRICT = "--strict" in sys.argv


def extract_wref_links(tex_file: Path):
    """
    Extract all \wref{target} links from a file.

    Returns list of (line_number, target) tuples.
    """
    try:
        content = tex_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {tex_file}: {e}")
        return []

    links = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if re.match(r'^\s*%', line):
            continue

        # Find all \wref{target} patterns
        # Handle both \wref{target} and \wref{target#section}
        for match in re.finditer(r'\\wref\{([^}]+)\}', line):
            target = match.group(1)

            # Strip section references (e.g., "note#sec:intro" -> "note")
            if '#' in target:
                target = target.split('#')[0]

            # Skip internal references (starting with #)
            if target.startswith('#'):
                continue

            links.append((line_num, target.strip()))

    return links


def get_available_notes():
    """Get set of all note names (stems without .tex extension)."""
    return {f.stem for f in NOTES_DIR.glob("*.tex")}


def validate_all_links():
    """Validate all links in all notes."""
    available_notes = get_available_notes()
    broken_links = defaultdict(list)  # {source_file: [(line, target), ...]}
    total_links = 0
    broken_count = 0

    for tex_file in sorted(NOTES_DIR.glob("*.tex")):
        links = extract_wref_links(tex_file)
        total_links += len(links)

        for line_num, target in links:
            if target not in available_notes:
                broken_links[tex_file.stem].append((line_num, target))
                broken_count += 1

    return broken_links, total_links, broken_count


def main():
    """Main validation function."""
    broken_links, total_links, broken_count = validate_all_links()

    if broken_count == 0:
        return 0

    print(f"⚠ {broken_count} broken link(s):")

    for source_file, links in sorted(broken_links.items()):
        for line_num, target in links:
            print(f"  {source_file}.tex:{line_num:04d} → \\wref{{{target}}}")

    if STRICT:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
