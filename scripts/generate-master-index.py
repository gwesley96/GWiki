#!/usr/bin/env python3
"""
GWiki Master Index Generator
Creates comprehensive indexes organized by tags, alphabetically, and chronologically
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO_ROOT / "notes"
METADATA_FILE = REPO_ROOT / ".gwiki-metadata.json"
OUTPUT_DIR = REPO_ROOT / "indices"


def load_metadata():
    """Load GWiki metadata"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {"creation_dates": {}, "forward_links": {}, "backlinks": {}}


def extract_note_metadata(tex_file):
    """Extract title, tags, and summary from a note"""
    content = tex_file.read_text()

    # Extract title
    title_match = re.search(r'\\Title\{([^}]+)\}', content)
    title = title_match.group(1) if title_match else tex_file.stem

    # Extract tags - handle multiple formats
    tags = []
    tags_match = re.search(r'\\Tags\{([^}]*)\}', content)
    if tags_match:
        raw = tags_match.group(1)
        # Split by comma or by } { pattern
        if ',' in raw:
            tags = [t.strip() for t in raw.split(',') if t.strip()]
        else:
            # Handle {tag1}{tag2} format
            tags = re.findall(r'\{([^}]+)\}', raw)
            if not tags:
                # Simple space-separated or single tag
                tags = [t.strip() for t in raw.split() if t.strip()]

    # Extract summary/topics
    summary = ""
    summary_match = re.search(r'\\(?:Summary|Topics)\{([^}]+)\}', content)
    if summary_match:
        summary = summary_match.group(1)

    # Extract aliases
    aliases = []
    aliases_match = re.search(r'\\Aliases\{([^}]+)\}', content)
    if aliases_match:
        # Split by comma
        raw_aliases = aliases_match.group(1)
        aliases = [a.strip() for a in raw_aliases.split(',') if a.strip()]

    return {
        "title": title,
        "tags": tags,
        "aliases": aliases,
        "summary": summary,
        "filename": tex_file.stem
    }


def generate_latex_index(notes_data, metadata, output_file, sort_by="title"):
    """Generate a LaTeX index file"""

    # Prepare header
    latex = r"""\documentclass{gwiki}
\usepackage{gwiki-links}

\Title{Master Index"""

    if sort_by == "tags":
        latex += " (by Tags)"
    elif sort_by == "date":
        latex += " (by Creation Date)"
    else:
        latex += " (Alphabetical)"

    latex += r"""}
\Tags{meta, index}

\begin{document}
\NoteHeader

This is a comprehensive index of all notes in GWiki.

"""

    if sort_by == "tags":
        # Group by tags
        tag_groups = defaultdict(list)
        untagged = []

        for note in notes_data:
            if note["tags"]:
                for tag in note["tags"]:
                    tag_groups[tag].append(note)
            else:
                untagged.append(note)

        # Sort tags alphabetically
        for tag in sorted(tag_groups.keys()):
            latex += f"\\section*{{{tag}}}\n\n"
            latex += "\\begin{lst}\n"
            for note in sorted(tag_groups[tag], key=lambda x: x["title"].lower()):
                latex += f"\\item \\wref{{{note['filename']}}}"
                if note["summary"]:
                    latex += f" --- {note['summary']}"
                latex += "\n"
            latex += "\\end{lst}\n\n"

        if untagged:
            latex += "\\section*{Untagged}\n\n"
            latex += "\\begin{lst}\n"
            for note in sorted(untagged, key=lambda x: x["title"].lower()):
                latex += f"\\item \\wref{{{note['filename']}}}\n"
            latex += "\\end{lst}\n\n"

    elif sort_by == "date":
        # Group by creation date
        dated_notes = []
        undated = []

        creation_dates = metadata.get("creation_dates", {})

        for note in notes_data:
            if note["filename"] in creation_dates:
                dated_notes.append((creation_dates[note["filename"]], note))
            else:
                undated.append(note)

        # Sort by date (newest first)
        dated_notes.sort(key=lambda x: x[0], reverse=True)

        current_year = None
        for date_str, note in dated_notes:
            year = date_str.split("-")[0]
            if year != current_year:
                latex += f"\\section*{{{year}}}\n\n"
                current_year = year

            latex += f"\\textbf{{{date_str}}}: \\wref{{{note['filename']}}}"
            if note["tags"]:
                latex += f" [{', '.join(note['tags'])}]"
            latex += "\n\n"

        if undated:
            latex += "\\section*{Undated}\n\n"
            latex += "\\begin{lst}\n"
            for note in sorted(undated, key=lambda x: x["title"].lower()):
                latex += f"\\item \\wref{{{note['filename']}}}\n"
            latex += "\\end{lst}\n\n"

    else:
        # Alphabetical grouping
        groups = defaultdict(list)

        for note in notes_data:
            first_char = note["title"][0].upper()
            if first_char.isalpha():
                groups[first_char].append(note)
            else:
                groups["#"].append(note)

        for letter in sorted(groups.keys()):
            latex += f"\\section*{{{letter}}}\n\n"
            latex += "\\begin{lst}\n"
            for note in sorted(groups[letter], key=lambda x: x["title"].lower()):
                latex += f"\\item \\wref{{{note['filename']}}}"
                if note["tags"]:
                    latex += f" [{', '.join(note['tags'])}]"
                latex += "\n"
            latex += "\\end{lst}\n\n"

    latex += r"""
\end{document}
"""

    output_file.write_text(latex)


def generate_html_index(notes_data, metadata):
    """Generate a beautiful HTML index page"""

    creation_dates = metadata.get("creation_dates", {})

    # Build tag index
    tag_groups = defaultdict(list)
    for note in notes_data:
        for tag in note["tags"]:
            tag_groups[tag].append(note)

    # Sort notes alphabetically
    alphabetical = sorted(notes_data, key=lambda x: x["title"].lower())

    # Recent notes
    recent_notes = []
    for note in notes_data:
        if note["filename"] in creation_dates:
            recent_notes.append((creation_dates[note["filename"]], note))
    recent_notes.sort(key=lambda x: x[0], reverse=True)
    recent_notes = recent_notes[:10]  # Top 10 most recent

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GWiki - Master Index</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            color: #1f2937;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        header {
            text-align: center;
            color: white;
            margin-bottom: 60px;
        }
        header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        header p {
            font-size: 1.2em;
            opacity: 0.95;
        }
        .search-box {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .search-box input {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-family: inherit;
        }
        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab {
            background: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .tab:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .content-panel {
            display: none;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .content-panel.active {
            display: block;
        }
        .note-list {
            list-style: none;
        }
        .note-item {
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
            transition: background 0.2s;
        }
        .note-item:last-child {
            border-bottom: none;
        }
        .note-item:hover {
            background: #f9fafb;
        }
        .note-link {
            color: #2563eb;
            text-decoration: none;
            font-size: 1.1em;
            font-weight: 500;
        }
        .note-link:hover {
            text-decoration: underline;
        }
        .note-tags {
            display: inline-flex;
            gap: 6px;
            margin-left: 10px;
            flex-wrap: wrap;
        }
        .tag {
            background: #dbeafe;
            color: #1e40af;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-family: monospace;
        }
        .note-summary {
            color: #6b7280;
            font-size: 0.95em;
            margin-top: 5px;
        }
        .tag-section {
            margin-bottom: 30px;
        }
        .tag-section h3 {
            color: #1e40af;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e5e7eb;
        }
        .alpha-section {
            margin-bottom: 25px;
        }
        .alpha-section h3 {
            color: #1e40af;
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #6b7280;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .recent-date {
            color: #6b7280;
            font-size: 0.9em;
            font-family: monospace;
            margin-right: 10px;
        }
        footer {
            text-align: center;
            color: white;
            margin-top: 60px;
            padding: 20px;
            opacity: 0.9;
        }
        footer a {
            color: white;
            text-decoration: none;
            font-weight: 600;
        }
        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>GWiki</h1>
            <p>A mathematical knowledge base</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">""" + str(len(notes_data)) + """</div>
                <div class="stat-label">Total Notes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(len(tag_groups)) + """</div>
                <div class="stat-label">Tags</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">""" + str(sum(len(links) for links in metadata.get("forward_links", {}).values())) + """</div>
                <div class="stat-label">Total Links</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search notes by title, tags, or content..." />
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('all')">All Notes</button>
            <button class="tab" onclick="showTab('tags')">By Tag</button>
            <button class="tab" onclick="showTab('recent')">Recent</button>
        </div>

        <div id="all-panel" class="content-panel active">
            <h2 style="margin-bottom: 20px; color: #1e40af;">All Notes (Alphabetical)</h2>
"""

    # All notes alphabetically
    current_letter = None
    for note in alphabetical:
        first_char = note["title"][0].upper()
        if first_char != current_letter:
            if current_letter is not None:
                html += "            </ul>\n            </div>\n"
            current_letter = first_char
            html += f'            <div class="alpha-section">\n'
            html += f'                <h3>{current_letter}</h3>\n'
            html += '                <ul class="note-list">\n'

        html += '                    <li class="note-item">\n'
        html += f'                        <a href="html/{note["filename"]}.html" class="note-link">{note["title"]}</a>\n'
        if note["tags"]:
            html += '                        <div class="note-tags">\n'
            for tag in note["tags"]:
                html += f'                            <span class="tag">{tag}</span>\n'
            html += '                        </div>\n'
        if note["summary"]:
            html += f'                        <div class="note-summary">{note["summary"]}</div>\n'
        html += '                    </li>\n'

    if current_letter is not None:
        html += "                </ul>\n            </div>\n"

    html += """        </div>

        <div id="tags-panel" class="content-panel">
            <h2 style="margin-bottom: 20px; color: #1e40af;">Notes by Tag</h2>
"""

    # By tags
    for tag in sorted(tag_groups.keys()):
        html += f'            <div class="tag-section">\n'
        html += f'                <h3>{tag} ({len(tag_groups[tag])})</h3>\n'
        html += '                <ul class="note-list">\n'
        for note in sorted(tag_groups[tag], key=lambda x: x["title"].lower()):
            html += '                    <li class="note-item">\n'
            html += f'                        <a href="html/{note["filename"]}.html" class="note-link">{note["title"]}</a>\n'
            html += '                    </li>\n'
        html += '                </ul>\n'
        html += '            </div>\n'

    html += """        </div>

        <div id="recent-panel" class="content-panel">
            <h2 style="margin-bottom: 20px; color: #1e40af;">Recently Created</h2>
            <ul class="note-list">
"""

    # Recent notes
    for date_str, note in recent_notes:
        html += '                <li class="note-item">\n'
        html += f'                    <span class="recent-date">{date_str}</span>\n'
        html += f'                    <a href="html/{note["filename"]}.html" class="note-link">{note["title"]}</a>\n'
        if note["tags"]:
            html += '                    <div class="note-tags">\n'
            for tag in note["tags"]:
                html += f'                        <span class="tag">{tag}</span>\n'
            html += '                    </div>\n'
        html += '                </li>\n'

    html += """            </ul>
        </div>

        <footer>
            <p>Generated by GWiki | <a href="https://greysonwesley.com">greysonwesley.com</a></p>
        </footer>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all panels
            document.querySelectorAll('.content-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            // Deactivate all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            // Show selected panel
            document.getElementById(tabName + '-panel').classList.add('active');
            // Activate clicked tab
            event.target.classList.add('active');
        }

        // Simple search functionality
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const noteItems = document.querySelectorAll('.note-item');

            noteItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    </script>
</body>
</html>
"""

    return html


def main():
    """Generate all index files"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load metadata
    metadata = load_metadata()

    # Scan all notes
    notes_data = []
    
    # Store real notes separately to avoid processing aliases in generate_latex_index if desired,
    # or just flag them.
    
    for tex_file in sorted(NOTES_DIR.glob("*.tex")):
        # Skip demo/debug files
        if "demo" in tex_file.stem or "debug" in tex_file.stem:
            continue

        note_meta = extract_note_metadata(tex_file)
        notes_data.append(note_meta)
        
        # Create alias entries
        for alias in note_meta["aliases"]:
            notes_data.append({
                "title": alias,
                "tags": note_meta["tags"],
                "summary": f"Alias for {note_meta['title']}",
                "filename": note_meta["filename"],
                "is_alias": True
            })

    print(f"Found {len(notes_data)} entries (including aliases)")

    # Generate LaTeX indices
    generate_latex_index(notes_data, metadata, OUTPUT_DIR / "index-alphabetical.tex", "title")
    print("✓ indices/index-alphabetical.tex")

    generate_latex_index(notes_data, metadata, OUTPUT_DIR / "index-by-tag.tex", "tags")
    print("✓ indices/index-by-tag.tex")

    generate_latex_index(notes_data, metadata, OUTPUT_DIR / "index-chronological.tex", "date")
    print("✓ indices/index-chronological.tex")

    # Generate HTML index
    html_content = generate_html_index(notes_data, metadata)
    html_output = REPO_ROOT / "index.html"
    html_output.write_text(html_content)
    print(f"✓ index.html")

    print(f"\nGenerated {len(notes_data)} note entries across 4 index files")


if __name__ == "__main__":
    main()
