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
    if '\\Title{' in content:
        start = content.find('\\Title{') + 7
        balance = 1
        i = start
        while i < len(content) and balance > 0:
            if content[i] == '{': balance += 1
            elif content[i] == '}': balance -= 1
            i += 1
        if balance == 0:
            meta['title'] = content[start:i-1]

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
  \item Total Notes: ''' + str(num_notes) + r'''
  \item Total Tags: ''' + str(num_tags) + r'''
  \item Total Aliases: ''' + str(num_aliases) + r'''
  \item Generated: ''' + datetime.now().strftime("%Y-%m-%d %H:%M") + r'''
\end{itemize}

\section{Notes by Tag}

'''

    # Sort tags alphabetically
    for tag in sorted(all_tags):
        tag_notes = tags_index[tag]
        latex += f"\\subsection{{{tag}}}\n\n"
        latex += "\\begin{itemize}[nosep,leftmargin=*]\n"

        for note in sorted(tag_notes, key=lambda n: (n['title'] or n['filename']).lower()):
            filename = note['filename']
            # title = note['title'] or note['filename'] # Unused variable
            latex += f"  \\item \\wref{{{filename}}}"
            if note['summary']:
                latex += f" — {note['summary'][:100]}"
                if len(note['summary']) > 100:
                    latex += "..."
            latex += "\n"

        latex += "\\end{itemize}\n\n"

    # Aliases section
    if all_aliases:
        latex += r'''\section{All Aliases}

This section lists all defined aliases across the vault.

\begin{itemize}[nosep,leftmargin=*]
'''

        for alias, title in sorted(all_aliases, key=lambda x: x[0].lower()):
            latex += f"  \\item \\textbf{{{alias}}} $\\rightarrow$ {title}\n"

        latex += r'''\end{itemize}
'''

    # All Notes (Alphabetical) - Moved to bottom
    latex += r'''\section{All Notes (Alphabetical)}

\begin{itemize}[nosep,leftmargin=*]
'''

    # Sort notes alphabetically by title
    sorted_notes = sorted(notes, key=lambda n: (n['title'] or n['filename']).lower())

    for note in sorted_notes:
        filename = note['filename']
        tags_str = ", ".join(note['tags']) if note['tags'] else ""
        
        # Clean title of texorpdfstring if present
        # We need a simple helper or just regex here since we don't import tex-to-html
        # But wait, we can just simplistic regex it?
        # Or better, just strip it.
        # \texorpdfstring{A}{B} -> A
        # Using a loop here is safer.
        current_title = note['title'] or filename
        while r'\texorpdfstring' in current_title:
             # Find it
             idx = current_title.find(r'\texorpdfstring')
             if idx == -1: break
             
             # Assume brace balanced structure {A}{B}
             # Parse A
             p1_start = current_title.find('{', idx)
             if p1_start == -1: break
             
             # Balance A
             bal = 1
             p1_end = p1_start + 1
             while p1_end < len(current_title) and bal > 0:
                 if current_title[p1_end] == '{': bal += 1
                 elif current_title[p1_end] == '}': bal -= 1
                 p1_end += 1
             
             tex_part = current_title[p1_start+1:p1_end-1]
             
             # Parse B (immediately follows?)
             p2_start = current_title.find('{', p1_end)
             # Consume space?
             
             # Should replace whole command with tex_part
             # But we need to find end of B to consume it.
             if p2_start != -1:
                 bal = 1
                 p2_end = p2_start + 1
                 while p2_end < len(current_title) and bal > 0:
                     if current_title[p2_end] == '{': bal += 1
                     elif current_title[p2_end] == '}': bal -= 1
                     p2_end += 1
                 
                 current_title = current_title[:idx] + tex_part + current_title[p2_end:]
             else:
                 break

        latex += f"  \\item \\wref[{current_title}]{{{filename}}} "
        if note['summary']:
            # Use raw summary to avoid double escaping problems in tex-to-html
            latex += f"— {note['summary'][:100]}{'...' if len(note['summary']) > 100 else ''} "
        
        if tags_str:
            latex += f" <i>({tags_str})</i>"
            
        latex += "\n"

    latex += r'''\end{itemize}

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
