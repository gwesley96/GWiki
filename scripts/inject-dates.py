#!/usr/bin/env python3
"""
Inject creation dates into LaTeX compilation.

Creates a .gwiki-dates.sty file that LaTeX can read to get creation dates.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
METADATA_FILE = ROOT / ".gwiki-metadata.json"
OUTPUT_FILE = ROOT / "lib" / "gwiki-dates.sty"


def load_creation_dates():
    """Load creation dates from metadata."""
    if METADATA_FILE.exists():
        try:
            data = json.loads(METADATA_FILE.read_text())
            return data.get('creation_dates', {})
        except:
            return {}
    return {}


def generate_dates_package():
    """Generate LaTeX package with creation date commands."""
    dates = load_creation_dates()

    lines = [
        "\\NeedsTeXFormat{LaTeX2e}",
        "\\ProvidesPackage{gwiki-dates}[2025/12/09 Auto-generated creation dates]",
        "",
        "% Auto-generated creation dates from .gwiki-metadata.json",
        "% Do not edit manually",
        "",
    ]

    # Create a command for each note
    for note_name, creation_date in sorted(dates.items()):
        # Escape special chars in note name for LaTeX command
        cmd_name = note_name.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('–', '')
        lines.append(f"\\providecommand{{\\gwikicreated{cmd_name}}}{{{creation_date}}}")

    lines.append("")
    lines.append("\\endinput")

    OUTPUT_FILE.write_text('\n'.join(lines))


if __name__ == "__main__":
    generate_dates_package()
