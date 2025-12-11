#!/usr/bin/env python3
"""
Import notes from Obsidian vault to GWiki
Converts markdown to LaTeX while preserving math and structure
"""

import re
import sys
from pathlib import Path
from datetime import datetime

OBSIDIAN_VAULT = Path("/Users/greysonwesley/Desktop/workflow/wiki")
GWIKI_NOTES = Path(__file__).resolve().parent.parent / "notes"


def extract_obsidian_metadata(content):
    """Extract YAML frontmatter from Obsidian note"""
    tags = []
    created = None

    # Match YAML frontmatter
    yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)

        # Extract tags
        tags_match = re.search(r'tags:\s*\n((?:  - .*\n)+)', yaml_content)
        if tags_match:
            tag_lines = tags_match.group(1)
            tags = [line.strip('- ').strip() for line in tag_lines.split('\n') if line.strip()]

        # Extract creation date
        created_match = re.search(r'date created:\s*(.+)', yaml_content)
        if created_match:
            created = created_match.group(1)

    return tags, created


def convert_obsidian_wikilinks(text):
    """Convert [[wikilink]] to \\wref{wikilink}"""
    # Handle [[link|display]] format
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\\wref[\2]{\1}', text)
    # Handle [[link]] format
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\\wref{\1}', text)
    return text


def convert_obsidian_to_latex(md_path):
    """Convert an Obsidian markdown note to GWiki LaTeX"""

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    tags, created = extract_obsidian_metadata(content)

    # Remove YAML frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Get title from filename
    title = md_path.stem

    # Convert wikilinks BEFORE other conversions
    content = convert_obsidian_wikilinks(content)

    # Convert markdown headers to sections (BEFORE bold/italic to avoid conflicts)
    content = re.sub(r'^### (.+)$', r'\\subsubsection*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'\\subsection*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.+)$', r'\\section*{\1}', content, flags=re.MULTILINE)

    # Convert **bold** to \textbf{} - must handle nested cases
    content = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', content)

    # Convert *italic* to \textit{} - avoid matching **
    # Only match single * not preceded or followed by another *
    def replace_italic(match):
        return f'\\textit{{{match.group(1)}}}'
    content = re.sub(r'(?<![*\w])\*([^*\n]+?)\*(?![*\w])', replace_italic, content)

    # LaTeX math is already in $ $ or \[ \], so leave it alone

    # Build LaTeX document
    tags_str = ', '.join(tags) if tags else ''

    latex = f"""\\documentclass{{gwiki}}
\\usepackage{{gwiki-links}}

\\Title{{{title}}}
\\Tags{{{tags_str}}}

\\begin{{document}}
\\NoteHeader

{content.strip()}

\\end{{document}}
"""

    return latex


def import_note(md_filename):
    """Import a single note from Obsidian to GWiki"""
    md_path = OBSIDIAN_VAULT / md_filename

    if not md_path.exists():
        print(f"✗ Not found: {md_filename}")
        return False

    # Convert to LaTeX
    latex_content = convert_obsidian_to_latex(md_path)

    # Write to GWiki notes directory
    tex_path = GWIKI_NOTES / f"{md_path.stem}.tex"
    tex_path.write_text(latex_content)

    print(f"✓ Imported: {md_filename} → notes/{md_path.stem}.tex")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: import-from-obsidian.py <note1.md> [note2.md] ...")
        print("\nOr use 'list' to see available notes:")
        print("  import-from-obsidian.py list | head -20")
        sys.exit(1)

    if sys.argv[1] == "list":
        for md_file in sorted(OBSIDIAN_VAULT.glob("*.md")):
            print(md_file.name)
        return

    count = 0
    for md_filename in sys.argv[1:]:
        if import_note(md_filename):
            count += 1

    print(f"\n✓ Imported {count} notes")


if __name__ == "__main__":
    main()
