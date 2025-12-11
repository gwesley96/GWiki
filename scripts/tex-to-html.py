#!/usr/bin/env python3
"""
GWiki LaTeX to HTML Converter
Converts GWiki LaTeX notes to standalone HTML pages with MathJax and TikZJax
"""

import re
import sys
import os
from pathlib import Path
from datetime import datetime

def extract_metadata(content):
    """Extract title and tags from LaTeX source"""
    title_match = re.search(r'\\Title\{([^}]+)\}', content)
    tags_match = re.search(r'\\Tags\{([^}]*)\}', content)

    title = title_match.group(1) if title_match else "Untitled"
    tags_raw = tags_match.group(1) if tags_match else ""
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()]

    return title, tags

def extract_body(content):
    r"""Extract content between \NoteHeader and \References"""
    # Find content between \NoteHeader and one of: \References, \Footer, \end{document}
    # But need to handle \end{document} inside code blocks
    # Strategy: First extract from \NoteHeader to the first \References or \Footer
    # If those don't exist, go to \end{document} but skip any inside ```...```

    # Try \References or \Footer first (these are unambiguous)
    match = re.search(r'\\NoteHeader\s*(.*?)(?=\\References\b|\\Footer\b)', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no \References or \Footer, extract to the OUTER \end{document}
    # (not one inside a code block)
    match = re.search(r'\\NoteHeader\s*(.*)', content, re.DOTALL)
    if match:
        body = match.group(1)
        # Find the last \end{document} (the outer one)
        last_end = body.rfind(r'\end{document}')
        if last_end != -1:
            return body[:last_end].strip()
        return body.strip()

    return ""

def convert_wikilinks(text):
    """Convert \wref links to HTML links (supports optional display moved before or after)."""
    def repl(match):
        display = match.group('display') or match.group('display_after') or match.group('target')
        target = match.group('target')
        return f'<a href="{target}.html">{display}</a>'

    pattern = re.compile(
        r'\\wref(?:\[(?P<display>[^\]]+)\])?\{(?P<target>[^}]+)\}(?:\[(?P<display_after>[^\]]+)\])?'
    )
    return pattern.sub(repl, text)

def convert_bold(text):
    """Convert **bold** to <strong>bold</strong>"""
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text

def convert_italic(text):
    """Convert *italic* to <em>italic</em>"""
    # Be careful not to match ** patterns or single * that are terminal objects
    # Only match *word* patterns, not standalone *
    text = re.sub(r'(?<!\*)\*(?!\*)([a-zA-Z][^*]+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    return text

def convert_tikz(text):
    """Convert tikz code blocks and inline tikzcd diagrams to TikZJax script tags."""
    tikz_blocks = []

    def stash_block(match):
        tikz_blocks.append(match.group(0))
        return f'__TIKZ_BLOCK_{len(tikz_blocks) - 1}__'

    # Temporarily remove fenced TikZ blocks so inline replacements don't see them
    text = re.sub(r'```tikz\s*(.*?)\s*```', stash_block, text, flags=re.DOTALL)

    def render_tikzcd(inner):
        inner = inner.strip()
        script = f'<script type="text/tikz">\\begin{{tikzpicture}}\\begin{{tikzcd}}{inner}\\end{{tikzcd}}\\end{{tikzpicture}}</script>'
        return script.replace('\\begin{tikzcd}', '__TIKZCD_BEGIN__').replace('\\end{tikzcd}', '__TIKZCD_END__')

    # Replace display math wrapped tikzcd environments
    text = re.sub(
        r'\\\[\s*\\begin\{tikzcd\}(.*?)\\end\{tikzcd\}\s*\\\]',
        lambda m: render_tikzcd(m.group(1)),
        text,
        flags=re.DOTALL
    )
    text = re.sub(
        r'\\begin\{tikzcd\}(.*?)\\end\{tikzcd\}',
        lambda m: render_tikzcd(m.group(1)),
        text,
        flags=re.DOTALL
    )

    def convert_block(block_text):
        tikzcd_match = re.search(r'\\begin\{tikzcd\}(.*?)\\end\{tikzcd\}', block_text, re.DOTALL)
        if tikzcd_match:
            tikzcd_content = tikzcd_match.group(1).strip()
            return render_tikzcd(tikzcd_content)
        return block_text

    # Restore fencing placeholders with converted content
    for idx, block in enumerate(tikz_blocks):
        placeholder = f'__TIKZ_BLOCK_{idx}__'
        converted = convert_block(block)
        text = text.replace(placeholder, converted)

    # Revert temporary placeholders so the TikZ code is valid again
    text = text.replace('__TIKZCD_BEGIN__', '\\begin{tikzcd}')
    text = text.replace('__TIKZCD_END__', '\\end{tikzcd}')

    return text

def convert_environments(text):
    """Convert LaTeX environments to HTML divs"""
    # Pattern to match \begin{envname}[optional] ... \end{envname}
    def replace_env(match):
        env_name = match.group(1)
        optional = match.group(2) if match.group(2) else ""
        body = match.group(3)

        # Remove \label{...} commands
        body = re.sub(r'\\label\{[^}]+\}', '', body)

        # Handle optional argument (usually the title)
        title = ""
        if optional:
            title = f"<strong>{env_name.capitalize()} ({optional}).</strong> "
        else:
            title = f"<strong>{env_name.capitalize()}.</strong> "

        return f'<div class="{env_name}">{title}{body}</div>'

    # Match \begin{env}[optional]{body}\end{env} or \begin{env}{body}\end{env}
    text = re.sub(
        r'\\begin\{(definition|theorem|lemma|proposition|corollary|example|remark)\}(?:\[([^\]]+)\])?(.*?)\\end\{\1\}',
        replace_env,
        text,
        flags=re.DOTALL
    )

    return text

def convert_itemize(text):
    """Convert list items to proper HTML lists"""
    lines = text.split('\n')
    result = []
    in_list = False
    list_type = None  # 'ul' for unordered, 'ol' for ordered
    current_item_lines = []
    base_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for list item patterns
        # Match "- " or "- (label) " where label is (i), (ii), (1), (2), etc.
        unordered_match = re.match(r'^(\s*)-\s+(?!\([ivxIVX0-9]+\)\s)(.*)$', line)
        ordered_match = re.match(r'^(\s*)-\s+\(([ivxIVX0-9]+)\)\s+(.*)$', line)

        if unordered_match and not ordered_match:
            # Unordered list item
            indent = unordered_match.group(1)
            item_content = unordered_match.group(2).strip()

            if not in_list or list_type != 'ul':
                if in_list:
                    # Close previous list item
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                result.append('<ul>')
                in_list = True
                list_type = 'ul'
                base_indent = len(indent)
            else:
                # Save previous item
                if current_item_lines:
                    result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                    current_item_lines = []

            current_item_lines.append(item_content)

        elif ordered_match:
            # Ordered list item with label
            indent = ordered_match.group(1)
            label = ordered_match.group(2)
            item_content = ordered_match.group(3).strip()

            if not in_list or list_type != 'ol':
                if in_list:
                    # Close previous list item
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                result.append('<ol>')
                in_list = True
                list_type = 'ol'
                base_indent = len(indent)
            else:
                # Save previous item
                if current_item_lines:
                    result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                    current_item_lines = []

            current_item_lines.append(item_content)

        else:
            # Not a list item start
            if in_list and line.strip():
                # Check if this line is indented and continues the previous item
                # OR if it's display math (starts with \[ or is just \])
                line_indent = len(line) - len(line.lstrip())
                is_display_math = stripped.startswith('\\[') or stripped == '\\]'
                if line_indent > base_indent or is_display_math:
                    # Continuation of current item
                    current_item_lines.append(line.strip())
                else:
                    # End of list
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                    result.append(line)
            elif in_list and not line.strip():
                # Empty line in list - could be end or spacing
                # Look ahead to see if more list items follow
                next_is_list = False
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.match(r'^\s*-\s+', next_line):
                        next_is_list = True

                if not next_is_list:
                    # End list
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                result.append(line)
            else:
                result.append(line)

        i += 1

    # Close any open list at end
    if in_list:
        if current_item_lines:
            result.append('<li>' + ' '.join(current_item_lines) + '</li>')
        result.append(f'</{list_type}>')

    return '\n'.join(result)

def convert_sections(text):
    """Convert markdown-style headers and LaTeX sections to HTML"""
    # Convert #### to h4
    text = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    # Convert ### to h3
    text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    # Convert ## to h2
    text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    return text

def convert_seealso(text):
    """Convert \SeeAlso command"""
    def replace_seealso(match):
        content = match.group(1)
        # Split by comma
        items = [item.strip() for item in content.split(',')]
        # Convert to links
        links = [f'<a href="{item}.html">{item}</a>' for item in items]
        return f'<p><strong>See also:</strong> {", ".join(links)}</p>'

    text = re.sub(r'\\SeeAlso\{([^}]+)\}', replace_seealso, text)
    return text

def wrap_paragraphs(text):
    """Wrap text paragraphs in <p> tags"""
    lines = text.split('\n')
    result = []
    in_tag = False
    in_script = False
    para_buffer = []

    for line in lines:
        stripped = line.strip()

        # Check if we're starting or ending a script tag
        if '<script' in stripped:
            # Flush paragraph buffer
            if para_buffer:
                result.append('<p>' + ' '.join(para_buffer) + '</p>')
                para_buffer = []
            in_script = True
            result.append(line)
            if '</script>' in stripped:
                in_script = False
            continue

        if in_script:
            result.append(line)
            if '</script>' in stripped:
                in_script = False
            continue

        # Check if line starts an HTML tag (but not script, we handled that above)
        if stripped.startswith('<'):
            # Flush paragraph buffer
            if para_buffer:
                result.append('<p>' + ' '.join(para_buffer) + '</p>')
                para_buffer = []
            result.append(line)
            # Track if we're in a multi-line tag
            if not '>' in stripped or stripped.count('<') > stripped.count('>'):
                in_tag = True
            else:
                in_tag = False
        elif in_tag:
            result.append(line)
            if '>' in stripped:
                in_tag = False
        elif stripped == '':
            # Empty line - flush paragraph
            if para_buffer:
                result.append('<p>' + ' '.join(para_buffer) + '</p>')
                para_buffer = []
            result.append(line)
        else:
            # Regular text - add to paragraph buffer
            para_buffer.append(stripped)

    # Flush final paragraph
    if para_buffer:
        result.append('<p>' + ' '.join(para_buffer) + '</p>')

    return '\n'.join(result)

def get_last_modified(tex_path):
    """Get last modified date of the TeX file"""
    if os.path.exists(tex_path):
        mtime = os.path.getmtime(tex_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')

def extract_wikilinks(content):
    """Extract all wikilink targets from LaTeX content"""
    links = set()
    # Match \wref[display]{target} and \wref{target}
    for match in re.finditer(r'\\wref(?:\[[^\]]+\])?\{([^}]+)\}', content):
        target = match.group(1)
        # Remove any PDF anchors (e.g., file.pdf#page=...)
        if '.pdf' in target:
            continue
        links.add(target)
    return sorted(links)

def build_backlinks_map(notes_dir):
    """Build a map of note -> list of notes that link to it"""
    backlinks = {}
    note_files = {}

    # First, get all note files
    for filepath in Path(notes_dir).glob('*.tex'):
        basename = filepath.stem
        note_files[basename] = filepath
        backlinks[basename] = []

    # Now scan each file for links
    for source_name, filepath in note_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            links = extract_wikilinks(content)
            for target in links:
                if target in backlinks:
                    backlinks[target].append(source_name)
        except Exception:
            continue

    return backlinks

def convert_to_html(tex_path, backlinks_map=None):
    """Main conversion function"""
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    title, tags = extract_metadata(content)
    body = extract_body(content)
    last_modified = get_last_modified(tex_path)

    # Get outgoing links and backlinks
    outgoing_links = extract_wikilinks(content)
    note_name = Path(tex_path).stem
    backlinks = backlinks_map.get(note_name, []) if backlinks_map else []

    # Convert body
    # Important: Do tikz/bold/italic/wikilinks BEFORE environments
    # to avoid issues with nested conversions
    body = convert_tikz(body)
    body = convert_wikilinks(body)
    body = convert_bold(body)
    body = convert_italic(body)
    body = convert_environments(body)  # This should come after basic conversions
    body = convert_itemize(body)  # Lists must come before sections
    body = convert_sections(body)
    body = convert_seealso(body)
    body = wrap_paragraphs(body)

    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="https://tikzjax.com/v1/fonts.css">
    <script>
    window.MathJax = {{
        tex: {{
            inlineMath: [['$', '$']],
            displayMath: [['\\\\[', '\\\\]']],
            macros: {{
                // Category theory
                cC: '\\\\mathcal{{C}}',
                cD: '\\\\mathcal{{D}}',
                cF: '\\\\mathcal{{F}}',
                cG: '\\\\mathcal{{G}}',
                cH: '\\\\mathcal{{H}}',
                cL: '\\\\mathcal{{L}}',
                cM: '\\\\mathcal{{M}}',
                cP: '\\\\mathcal{{P}}',
                cU: '\\\\mathcal{{U}}',
                Obj: '\\\\operatorname{{Obj}}',
                Hom: '\\\\operatorname{{Hom}}',
                Mor: '\\\\operatorname{{Mor}}',
                End: '\\\\operatorname{{End}}',
                Aut: '\\\\operatorname{{Aut}}',
                id: '\\\\mathrm{{id}}',

                // Blackboard bold
                bR: '\\\\mathbb{{R}}',
                bC: '\\\\mathbb{{C}}',
                bZ: '\\\\mathbb{{Z}}',
                bN: '\\\\mathbb{{N}}',
                bQ: '\\\\mathbb{{Q}}',

                // Categories
                Set: '\\\\mathbf{{Set}}',
                Grp: '\\\\mathbf{{Grp}}',
                Top: '\\\\mathbf{{Top}}',
                Vec: '\\\\mathbf{{Vec}}',

                // Operators
                colim: '\\\\operatorname{{colim}}',
                Ext: '\\\\operatorname{{Ext}}',
                Tor: '\\\\operatorname{{Tor}}',
                Spec: '\\\\operatorname{{Spec}}',
                im: '\\\\operatorname{{im}}',
                coker: '\\\\operatorname{{coker}}',
                coloneqq: '\\\\mathrel{{\\\\vcenter{{\\\\hbox{{.}}\\\\hbox{{.}}}}}}=',
                coloneq: '\\\\mathrel{{\\\\vcenter{{\\\\hbox{{.}}\\\\hbox{{.}}}}}}=',

                // TikZ-like (limited in HTML)
                to: '\\\\rightarrow',
                injto: '\\\\hookrightarrow',
                surjto: '\\\\twoheadrightarrow'
            }}
        }}
    }};
    </script>
    <script src="https://tikzjax.com/v1/tikzjax.js"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {{
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            font-family: Georgia, serif;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2563eb;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #1e40af;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #1e3a8a;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        h4 {{
            color: #1e40af;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .metadata {{
            font-size: 0.9em;
            color: #6b7280;
            margin-bottom: 20px;
            font-family: monospace;
        }}
        .topics {{
            background: #f3f4f6;
            padding: 15px;
            border-left: 4px solid #2563eb;
            margin: 20px 0;
        }}
        .idea {{
            background: #ecfeff;
            border: 1px solid #06b6d4;
            border-left: 4px solid #06b6d4;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .definition, .theorem, .example, .lemma, .proposition, .corollary, .remark {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 4px;
        }}
        .definition {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }}
        .theorem, .lemma, .proposition, .corollary {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
        }}
        .example {{
            background: #f3e8ff;
            border-left: 4px solid #a855f7;
        }}
        .remark {{
            background: #f3f4f6;
            border-left: 4px solid #6b7280;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        script[type="text/tikz"] {{
            display: block;
            margin: 20px 0;
            text-align: center;
        }}
        svg {{
            display: block;
            margin: 20px auto;
            max-width: 100%;
        }}
        .linked-notes, .backlinks {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
        .linked-notes h2, .backlinks h2 {{
            color: #1e40af;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .linked-notes ul, .backlinks ul {{
            list-style: none;
            padding-left: 0;
        }}
        .linked-notes li, .backlinks li {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="metadata">'''

    if tags:
        html += f'''
        <strong>Topics:</strong> {", ".join(tags)}<br>'''

    html += f'''
        <strong>Last modified:</strong> {last_modified}
    </div>

    <div class="content">
        {body}
    </div>'''

    # Add linked notes section if there are outgoing links
    if outgoing_links:
        html += '''

    <div class="linked-notes">
        <h2>Linked Notes</h2>
        <ul>'''
        for link in outgoing_links:
            html += f'''
            <li><a href="{link}.html">{link}</a></li>'''
        html += '''
        </ul>
    </div>'''

    # Add backlinks section if there are any
    if backlinks:
        html += '''

    <div class="backlinks">
        <h2>Backlinks</h2>
        <ul>'''
        for backlink in sorted(backlinks):
            html += f'''
            <li><a href="{backlink}.html">{backlink}</a></li>'''
        html += '''
        </ul>
    </div>'''

    html += '''
</body>
</html>
'''

    return html

def main():
    if len(sys.argv) < 2:
        print("Usage: tex-to-html.py <input.tex> [output.html]")
        sys.exit(1)

    tex_path = sys.argv[1]

    if not os.path.exists(tex_path):
        print(f"Error: {tex_path} not found")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        html_path = sys.argv[2]
    else:
        # Default: input.tex -> html/input.html
        basename = os.path.splitext(os.path.basename(tex_path))[0]
        html_path = os.path.join('html', f'{basename}.html')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(html_path) or '.', exist_ok=True)

    # Build backlinks map from notes directory
    notes_dir = os.path.dirname(tex_path) or 'notes'
    backlinks_map = build_backlinks_map(notes_dir)

    # Convert
    html = convert_to_html(tex_path, backlinks_map)

    # Write output
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Converted: {tex_path} -> {html_path}")

if __name__ == '__main__':
    main()
