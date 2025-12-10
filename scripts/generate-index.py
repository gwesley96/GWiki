#!/usr/bin/env python3
"""
GWiki Vault Index Generator

Generates a comprehensive index.tex document showing:
- Vault statistics
- All notes alphabetically
- Notes organized by tag
- All aliases
- Quick reference hub for the entire vault
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent.parent
NOTES_DIR = ROOT / "notes"
OUTPUT = ROOT / "index.tex"
METADATA_FILE = ROOT / ".gwiki-metadata.json"

def load_creation_dates():
    """Load creation dates from metadata file."""
    if METADATA_FILE.exists():
        try:
            data = json.loads(METADATA_FILE.read_text())
            return data.get('creation_dates', {})
        except:
            return {}
    return {}

def parse_metadata(tex_file: Path) -> dict:
    """Extract metadata from a .tex file."""
    try:
        content = tex_file.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return None

    meta = {
        'filename': tex_file.stem,
        'title': None,
        'tags': [],
        'aliases': [],
        'summary': None,
    }

    # Extract \Title
    title_match = re.search(r'\\Title\{([^}]+)\}', content)
    if title_match:
        meta['title'] = title_match.group(1)

    # Extract \Tags - handle both {tag1}{tag2} and {tag1, tag2}
    tags_match = re.search(r'\\Tags(\{[^}]*\})+', content)
    if tags_match:
        tags_text = tags_match.group(0)
        # Extract all {...} groups
        tag_groups = re.findall(r'\{([^}]*)\}', tags_text)
        for group in tag_groups:
            # Split by comma and strip
            tags = [t.strip() for t in group.split(',') if t.strip()]
            meta['tags'].extend(tags)

    # Extract \Aliases
    aliases_match = re.search(r'\\Aliases\{([^}]*)\}', content)
    if aliases_match:
        aliases_text = aliases_match.group(1)
        meta['aliases'] = [a.strip() for a in aliases_text.split(',') if a.strip()]

    # Extract \Summary
    summary_match = re.search(r'\\Summary\{([^}]+)\}', content)
    if summary_match:
        meta['summary'] = summary_match.group(1)

    return meta

def latex_escape(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_index():
    """Generate the index.tex file."""

    # Scan all notes
    notes = []
    for tex_file in sorted(NOTES_DIR.glob("*.tex")):
        meta = parse_metadata(tex_file)
        if meta and meta['filename'] != 'index':  # Skip index itself
            notes.append(meta)

    # Organize by tags
    tags_index = defaultdict(list)
    all_tags = set()
    for note in notes:
        for tag in note['tags']:
            tags_index[tag].append(note)
            all_tags.add(tag)

    # Collect all aliases
    all_aliases = []
    for note in notes:
        for alias in note['aliases']:
            all_aliases.append((alias, note['title'] or note['filename']))

    # Statistics
    num_notes = len(notes)
    num_tags = len(all_tags)
    num_aliases = sum(len(n['aliases']) for n in notes)

    # Generate LaTeX
    latex = r'''\documentclass[11pt]{gwiki}

\Title{GWiki Vault Index}
\Summary{Comprehensive index and statistics for the entire GWiki vault.}

\begin{document}

\NoteHeader

\section{Vault Statistics}

\begin{itemize}[nosep]
  \item \textbf{Total Notes:} ''' + str(num_notes) + r'''
  \item \textbf{Total Tags:} ''' + str(num_tags) + r'''
  \item \textbf{Total Aliases:} ''' + str(num_aliases) + r'''
  \item \textbf{Generated:} ''' + datetime.now().strftime("%Y-%m-%d %H:%M") + r'''
\end{itemize}

\section{All Notes (Alphabetical)}

\begin{itemize}[nosep,leftmargin=*]
'''

    # Sort notes alphabetically by title
    sorted_notes = sorted(notes, key=lambda n: (n['title'] or n['filename']).lower())

    for note in sorted_notes:
        title = note['title'] or note['filename']
        filename = note['filename']
        tags = ', '.join(note['tags']) if note['tags'] else '(no tags)'

        latex += f"  \\item \\wref{{{filename}}} "
        if note['summary']:
            latex += f"--- {latex_escape(note['summary'][:80])}{'...' if len(note['summary']) > 80 else ''} "
        latex += f"\\hfill {{\\footnotesize\\color{{gray}}\\textit{{{latex_escape(tags)}}}}}\n"

    latex += r'''\end{itemize}

\section{Notes by Tag}

'''

    # Sort tags alphabetically
    for tag in sorted(all_tags):
        tag_notes = tags_index[tag]
        latex += f"\\subsection{{{latex_escape(tag)}}}\n\n"
        latex += "\\begin{itemize}[nosep,leftmargin=*]\n"

        for note in sorted(tag_notes, key=lambda n: (n['title'] or n['filename']).lower()):
            filename = note['filename']
            title = note['title'] or note['filename']
            latex += f"  \\item \\wref{{{filename}}}"
            if note['summary']:
                latex += f" --- {latex_escape(note['summary'][:60])}{'...' if len(note['summary']) > 60 else ''}"
            latex += "\n"

        latex += "\\end{itemize}\n\n"

    # Aliases section
    if all_aliases:
        latex += r'''\section{All Aliases}

This section lists all defined aliases across the vault.

\begin{itemize}[nosep,leftmargin=*]
'''

        for alias, title in sorted(all_aliases, key=lambda x: x[0].lower()):
            latex += f"  \\item \\textbf{{{latex_escape(alias)}}} $\\rightarrow$ {latex_escape(title)}\n"

        latex += r'''\end{itemize}
'''

    latex += r'''
\section{How to Use This Index}

\begin{itemize}[nosep]
  \item Click on any note title to open the corresponding PDF
  \item Browse by tag to find related notes
  \item Use the aliases section to find alternate names for concepts
  \item This index is regenerated automatically with \texttt{make index}
\end{itemize}

\Footer

\end{document}
'''

    # Write output
    OUTPUT.write_text(latex, encoding='utf-8')
    print(f"✓ Generated vault index: {OUTPUT}")
    print(f"  - {num_notes} notes")
    print(f"  - {num_tags} tags")
    print(f"  - {num_aliases} aliases")

if __name__ == "__main__":
    generate_index()
