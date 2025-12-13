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
    """Generate a beautiful, modern HTML index page"""
    
    # Calculate stats
    total_notes = len(notes_data)
    total_tags = len(set(t for n in notes_data for t in n["tags"]))
    total_links = sum(len(links) for links in metadata.get("forward_links", {}).values())

    # Build tag index
    tag_groups = defaultdict(list)
    for note in notes_data:
        for tag in note["tags"]:
            tag_groups[tag].append(note)

    # Sort notes
    alphabetical = sorted(notes_data, key=lambda x: x["title"].lower())
    
    # Recent notes
    creation_dates = metadata.get("creation_dates", {})
    recent_notes = []
    for note in notes_data:
        if note["filename"] in creation_dates:
            recent_notes.append((creation_dates[note["filename"]], note))
    recent_notes.sort(key=lambda x: x[0], reverse=True)
    recent_notes = recent_notes[:6] # Top 6 for the grid

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GWiki Index</title>
    <link rel="stylesheet" href="html/style.css">
    <style>
        /* Index-specific Overrides */
        body { padding-top: 0; }
        .hero {
            text-align: center;
            padding: 80px 20px 40px;
        }
        .hero h1 { font-size: 4rem; margin-bottom: 0.2em; }
        .hero p { font-size: 1.25rem; color: var(--text-muted); font-family: var(--font-body); font-weight: 300; }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 60px 0 30px;
            border-bottom: 2px solid var(--border);
            padding-bottom: 10px;
        }
        
        .section-header h2 { 
            margin: 0; 
            border: none; 
            font-size: 1.5rem; 
        }
        
        .filter-tabs {
            display: flex;
            gap: 20px;
        }
        
        .filter-btn {
            background: none;
            border: none;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            color: var(--text-muted);
            cursor: pointer;
            padding: 5px 0;
            position: relative;
        }
        
        .filter-btn.active { color: var(--text-main); font-weight: 600; }
        .filter-btn.active::after {
            content: '';
            position: absolute;
            bottom: -12px;
            left: 0;
            width: 100%;
            height: 2px;
            background: var(--text-main);
        }

        .view-panel { display: none; }
        .view-panel.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        
        <div class="hero">
            <h1>GWiki</h1>
            <p>Mathematical Knowledge Base</p>
            
            <div class="search-container">
                <input type="text" id="searchInput" class="search-input" placeholder="Search knowledge..." autofocus>
            </div>

            <div class="stats-row">
                <div class="stat-item">
                    <div class="value">""" + str(total_notes) + """</div>
                    <div class="label">Notes</div>
                </div>
                <div class="stat-item">
                    <div class="value">""" + str(total_tags) + """</div>
                    <div class="label">Topics</div>
                </div>
                <div class="stat-item">
                    <div class="value">""" + str(total_links) + """</div>
                    <div class="label">Connections</div>
                </div>
            </div>
        </div>

        <div class="section-header">
            <h2>Explore</h2>
            <div class="filter-tabs">
                <button class="filter-btn active" onclick="switchView('recent')">Fresh</button>
                <button class="filter-btn" onclick="switchView('all')">Index</button>
                <button class="filter-btn" onclick="switchView('tags')">Topics</button>
            </div>
        </div>

        <!-- Recent Grid -->
        <div id="view-recent" class="view-panel active">
            <div class="note-grid">
"""
    for date_str, note in recent_notes:
        html += f"""                <a href="html/{note['filename']}.html" class="note-card">
                    <div class="meta">
                        <span>{date_str}</span>
                    </div>
                    <h3>{note['title']}</h3>
                    <div class="excerpt">{note['summary'] if note['summary'] else 'No summary available.'}</div>
                    <div class="tags-row">
"""
        for tag in note["tags"][:3]: # Limit tags per card
            html += f'                        <span class="tag-chip">{tag}</span>\n'
        html += """                    </div>
                </a>
"""

    html += """            </div>
        </div>

        <!-- All Notes List (Grouped Alphabetically) -->
        <div id="view-all" class="view-panel">
            <div style="column-count: 2; column-gap: 40px;">
"""
    
    current_char = None
    for note in alphabetical:
        first_char = note["title"][0].upper()
        if first_char != current_char:
            if current_char: html += "</ul></div>\n"
            current_char = first_char
            html += f'<div style="break-inside: avoid; margin-bottom: 30px;">\n<h3 style="margin-top:0; border-bottom: 1px solid var(--border); padding-bottom: 5px;">{current_char}</h3>\n<ul style="list-style: none; padding: 0;">\n'
        
        html += f'<li style="margin-bottom: 8px;"><a href="html/{note["filename"]}.html" style="text-decoration: none; font-weight: 500;">{note["title"]}</a></li>\n'
    
    if current_char: html += "</ul></div>\n"

    html += """            </div>
        </div>

        <!-- Topics Cloud -->
        <div id="view-tags" class="view-panel">
             <div style="display: flex; flex-wrap: wrap; gap: 10px;">
"""
    for tag in sorted(tag_groups.keys()):
        count = len(tag_groups[tag])
        size = 1 + (count / 5) * 0.1 # Simple scaling
        html += f'<a href="#" onclick="filterByTag(\'{tag}\'); return false;" class="tag-chip" style="font-size: {size}rem; padding: 5px 10px;">{tag} ({count})</a>\n'

    html += """            </div>
            
            <div id="tag-results" style="margin-top: 30px; display: none;">
                <h3 id="tag-title">Notes tagged...</h3>
                <div class="note-grid" id="tag-grid"></div>
            </div>
        </div>

    </div>

    <script>
        const notesData = """ + json.dumps(notes_data) + """;
        const tagMap = """ + json.dumps({t: [n['filename'] for n in g] for t, g in tag_groups.items()}) + """;

        function switchView(viewName) {
            document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            
            document.getElementById('view-' + viewName).classList.add('active');
            // Find the button (approximate)
            event.target.classList.add('active');
        }

        function filterByTag(tag) {
            const results = document.getElementById('tag-results');
            const grid = document.getElementById('tag-grid');
            const title = document.getElementById('tag-title');
            
            results.style.display = 'block';
            title.textContent = '#' + tag;
            grid.innerHTML = '';

            const filenames = tagMap[tag] || [];
            
            // Inefficient but fine for client side small wiki
            const filteredNotes = notesData.filter(n => filenames.includes(n.filename));

            filteredNotes.forEach(note => {
                const card = document.createElement('a');
                card.href = 'html/' + note.filename + '.html';
                card.className = 'note-card';
                card.innerHTML = `<h3>${note.title}</h3><div class="excerpt">${note.summary || ''}</div>`;
                grid.appendChild(card);
            });
            
            // Scroll to results
            results.scrollIntoView({behavior: 'smooth'});
        }

        // Search
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const term = e.target.value.toLowerCase();
            if (term.length < 2) return;
            
            // If searching, maybe switch to a search view or just highlight?
            // For now, let's keep it simple: filter the 'All' view which is most useful
            switchView('all');
            
            const listItems = document.querySelectorAll('#view-all li');
            listItems.forEach(li => {
                const text = li.textContent.toLowerCase();
                li.style.display = text.includes(term) ? '' : 'none';
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
