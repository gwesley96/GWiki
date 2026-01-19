#!/usr/bin/env python3
"""
Obsidian to GWiki Migration Script
Converts Obsidian markdown notes to GWiki LaTeX format
"""

import re
import sys
import os
import subprocess
from pathlib import Path

def extract_frontmatter(content):
    """Extract YAML frontmatter from Obsidian note"""
    frontmatter = {}
    if content.startswith('---'):
        try:
            end = content.index('---', 3)
            fm_text = content[3:end].strip()

            # Parse YAML-like structure
            current_key = None
            for line in fm_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('- '):
                    # List item
                    if current_key:
                        if current_key not in frontmatter:
                            frontmatter[current_key] = []
                        frontmatter[current_key].append(line[2:].strip())
                elif ':' in line:
                    # Key-value pair
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    value = value.strip()
                    if value:
                        frontmatter[current_key] = value
                    else:
                        frontmatter[current_key] = []

            content = content[end+3:].lstrip()
        except ValueError:
            pass

    return frontmatter, content

def escape_latex_text(text):
    """Escape text for LaTeX display"""
    return text.replace('#', r'\#').replace('&', r'\&').replace('%', r'\%').replace('_', r'\_').replace('$', r'\$')

def escape_link_target(link):
    """Escape link target (keep # and _ for gwiki/hyperref)"""
    # We DO NOT escape # (anchors) or _ (filenames)
    # But we DO escape % and & just in case they mess up URL parsing or args
    return link.replace('&', r'\&').replace('%', r'\%')

def convert_wikilinks(text):
    """Convert Obsidian [[wikilinks]] to GWiki \wref{}"""

    def replace_header_link(match):
        # **Header.** [[link|text]] -> \wref[Header.]{link} text
        header = match.group(1)
        header = header.replace('**', '').strip()
        link = escape_link_target(match.group(2))
        body = match.group(3)
        return f'\\wref[{header}]{{{link}}} {body}'

    def replace_link(match):
        link = escape_link_target(match.group(1))
        display = escape_latex_text(match.group(2))
        if len(display) > 60:
             return f'{display} \\wcite{{{link}}}'
        return f'\\wref[{display}]{{{link}}}'
        
    def replace_simple_link(match):
        link = escape_link_target(match.group(1))
        # Display text is implicit, usually same as link but without anchor?
        # \wref{link} handles display automatically
        return f'\\wref{{{link}}}'

    # Special case: **Header.** [[link|text]]
    text = re.sub(r'\*\*([^\*]+)\*\*[:\.]?\s*\[\[([^\]|]+)\|([^\]]+)\]\]', replace_header_link, text)

    # [[link|display]] -> \wref[display]{link}
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', replace_link, text)
    # [[link]] -> \wref{link}
    text = re.sub(r'\[\[([^\]]+)\]\]', replace_simple_link, text)
    return text

def convert_markdown_links(text):
    """Convert Markdown [text](url) to \href or \wref"""
    def repl(match):
        display = escape_latex_text(match.group(1))
        url = match.group(2)
        
        # Check for external link
        if re.match(r'^[a-zA-Z]+://', url):
            clean_url = escape_link_target(url) # Keep # etc
            return f'\\href{{{clean_url}}}{{{display}}}'
        else:
            # Internal link
            clean_url = escape_link_target(url)
            # Strip .md if present
            if clean_url.endswith('.md'):
                clean_url = clean_url[:-3]
            return f'\\wref[{display}]{{{clean_url}}}'

    # Match [text](url) but NOT image ![]
    text = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)', repl, text)
    return text

def convert_hashtags(text):
    """Convert #tags to comments or remove them"""
    # Remove common workflow tags
    text = re.sub(r'#(todo|unfinished|organize-this|article)\b', '', text)
    
    # Keep other tags as comments, but ONLY if they look like tags (preceded by space or start of line)
    # This prevents matching # inside URLs or PDF links like file.pdf#page=1
    text = re.sub(r'(^|\s)#(\w+)', r'\1% Tag: \2', text)
    return text

def convert_formatting(text):
    """Convert Markdown formatting to LaTeX"""
    # Headers
    text = re.sub(r'(?m)^# (.*?)$', r'\\section{\1}', text)
    text = re.sub(r'(?m)^## (.*?)$', r'\\subsection{\1}', text)
    text = re.sub(r'(?m)^### (.*?)$', r'\\subsubsection{\1}', text)
    
    # Bold **text** -> \defn{text}
    text = re.sub(r'\*\*((?:[^*]|\*[^*])*?)\*\*', r'\\defn{\1}', text)
    
    # Italic *text* -> \textit{text}
    # Matches *text* but assumes it's not part of a math formula like $a*b$
    # We use a simple approximation: must not be surrounded by spaces on inside
    # (e.g. * text * is not italic)
    text = re.sub(r'(?<!\*)\*([^\s*](?:[^*]*[^\s*])?)\*(?!\*)', r'\\textit{\1}', text)
    
    # Theorem Environments
    # **Definition.** Content -> \begin{definition} Content \end{definition}
    # We support Definition, Theorem, Lemma, Proposition, Corollary, Example, Remark
    # Theorem Environments
    # **Definition.** Content -> \begin{definition} Content \end{definition}
    # **Example (Title).** Content -> \begin{example}[Title] Content \end{example}
    thumbs = ['Definition', 'Theorem', 'Lemma', 'Proposition', 'Corollary', 'Example', 'Remark', 'Note']
    
    def repl_thm(match):
        thm_type = match.group(1)
        title = match.group(2)
        content = match.group(3).strip()
        
        lower_thm = thm_type.lower()
        if title:
            return f'\\begin{{{lower_thm}}}[{title}]\n{content}\n\\end{{{lower_thm}}}'
        else:
            return f'\\begin{{{lower_thm}}}\n{content}\n\\end{{{lower_thm}}}'

    for thm in thumbs:
        # Regex matches: \defn{Type.} OR \defn{Type (Title).}
        # Group 1: Type
        # Group 2: Title (optional)
        # Group 3: Content
        pattern = r'\\defn\{(' + thm + r')(?:\s*\((.*?)\))?\.\}\s*(.*?)(?=\n\n|\Z)'
        text = re.sub(pattern, repl_thm, text, flags=re.DOTALL)

    return text

def convert_lists(text):
    """Convert markdown lists to lst environment"""
    lines = text.split('\n')
    new_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        # Handle both - and * as list markers
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                new_lines.append('\\begin{lst}')
                in_list = True
            content = stripped[2:]
            new_lines.append(f'  \\item {content}')
        else:
            if in_list and stripped:
                # If we hit a non-empty line that isn't a list item, end the list
                new_lines.append('\\end{lst}')
                in_list = False
            elif in_list and not stripped:
                # Empty line in list - usually keeps list going or ends it?
                # Markdown usually allows loose lists.
                # Let's keep it open unless next line is strictly non-list.
                pass
                
            new_lines.append(line)
            
    if in_list:
        new_lines.append('\\end{lst}')
        
    return '\n'.join(new_lines)

def convert_images(text):
    """Handle ![[image.png]] embeds"""
    # Convert to comments since GWiki doesn't have direct image support
    text = re.sub(r'!\[\[([^\]]+)\]\]', r'% Image: \1 (not migrated)', text)
    return text


def extract_title_from_filename(filename):
    """Extract title from filename"""
    # Remove .md extension
    title = filename.replace('.md', '')
    # Capitalize first letter of each word for proper nouns
    return title

def convert_to_gwiki(obsidian_path, tags_to_use=None):
    """Main conversion function"""
    with open(obsidian_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter, body = extract_frontmatter(content)

    # Get metadata
    tags = frontmatter.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]

    # Filter out workflow tags
    tags = [t for t in tags if t not in ['good', 'todo', 'unfinished', 'organize-this', 'article']]

    # Override with provided tags if given
    if tags_to_use:
        tags = tags_to_use

    aliases = frontmatter.get('aliases', [])
    if isinstance(aliases, str):
        aliases = [aliases]

    # Get title from filename
    filename = Path(obsidian_path).name
    title = extract_title_from_filename(filename)
    
    # Extract date created
    created_date = frontmatter.get('date created', '')
    
    # Extract nav
    prev_note = frontmatter.get('previous', '')
    next_note = frontmatter.get('next', '')

    # Also look for navigation in the body: [[Link]] (previous) or [[Link]] (next)
    # Regex to find these patterns
    # We look for lines that might be just this, or part of a list
    
    # Check for Next
    next_match = re.search(r'\[\[([^\]]+)\]\]\s*\(next\)', body, re.IGNORECASE)
    if next_match:
        if not next_note: # Frontmatter takes precedence? Or body? Let's say body if frontmatter empty
             next_note = next_match.group(1)
        # Remove from body
        body = body.replace(next_match.group(0), '')

    # Check for Previous
    prev_match = re.search(r'\[\[([^\]]+)\]\]\s*\(previous\)', body, re.IGNORECASE)
    if prev_match:
        if not prev_note:
             prev_note = prev_match.group(1)
        body = body.replace(prev_match.group(0), '')
    
    # Clean up empty list items left behind (e.g. "- ")
    body = re.sub(r'^\s*-\s*$', '', body, flags=re.MULTILINE)

    # Convert body
    # Order matters
    
    # Protect math first
    body, math_tokens = protect_math(body)

    
    body = convert_images(body)
    body = convert_wikilinks(body)
    body = convert_markdown_links(body)
    body = convert_hashtags(body)
    body = convert_formatting(body) # Headers, Bold, Italic
    body = convert_lists(body)      # Lists
    
    # Restore math (and handle spacing)
    body = restore_math(body, math_tokens)
    
    # Clean math spacing (only inside trimming)
    # body = clean_math(body)
    
    body = body.strip()

    # Build GWiki document
    gwiki_content = r'\documentclass{gwiki}' + '\n\n'
    gwiki_content += f'\\Title{{{title}}}' + '\n'

    if tags:
        gwiki_content += f'\\Tags{{{", ".join(tags)}}}' + '\n'
    else:
        gwiki_content += '\\Tags{}' + '\n'
        
    if created_date:
        gwiki_content += f'\\providecommand{{\\gwikicreateddate}}{{{created_date}}}' + '\n'
        
    if prev_note:
        # Handle [[link]] format if present
        if '[[' in prev_note:
            prev_note = prev_note.replace('[[', '').replace(']]', '')
        gwiki_content += f'\\PreviousNote{{{prev_note}}}' + '\n'

    if next_note:
         if '[[' in next_note:
            next_note = next_note.replace('[[', '').replace(']]', '')
         gwiki_content += f'\\NextNote{{{next_note}}}' + '\n'

    gwiki_content += '\n\\begin{document}\n\n'
    gwiki_content += '\\NoteHeader\n'
    gwiki_content += '\\NoteNavigation\n\n'

    # Add body
    gwiki_content += body + '\n\n'

    gwiki_content += '\\References\n\n'
    gwiki_content += '\\Footer\n\n'
    gwiki_content += '\\end{document}\n'

    return gwiki_content, title

def convert_math_macros(text):
    """Convert raw LaTeX macros to GWiki shortcuts (e.g. \mathbb{R} -> \bbR)"""
    # Mappings based on gwiki-macros.sty
    # patterns: (latex_cmd, gwiki_prefix)
    replacements = [
        ('mathbb', 'bb'),
        ('mathcal', 'c'),
        ('mathscr', 's'),
        ('mathfrak', 'f'),
        ('mathbf', 'bf'),
        ('mathsf', 'sf'),
        ('mathrm', 'r'), # Only matches single chars below
    ]
    
    for latex, gwiki in replacements:
        # Match \cmd{X} where X is a single letter A-Z or a-z
        pattern_braces = r'\\' + latex + r'\{([a-zA-Z])\}'
        text = re.sub(pattern_braces, f'\\\\{gwiki}\\1', text)
        
        # Match \cmd X where X is a single letter
        pattern_space = r'\\' + latex + r'\s+([a-zA-Z])(?![a-zA-Z])'
        text = re.sub(pattern_space, f'\\\\{gwiki}\\1', text)
        
    # Standardize inequalities: \le -> \leq, \ge -> \geq
    text = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', text)
    text = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', text)
        
    return text

def protect_math(text):
    """Temporarily replace math blocks with tokens"""
    tokens = []
    
    def replace_func(match):
        token = f"__MATH_TOKEN_{len(tokens)}__"
        content = match.group(0)
        # Convert macros inside math
        content = convert_math_macros(content)
        tokens.append(content)
        return token

    # Block math $$...$$
    text = re.sub(r'(?s)\$\$.*?\$\$', replace_func, text)
    # Inline math $...$
    text = re.sub(r'(?<!\\)\$(?:\\.|[^$])+\$(?!\d)', replace_func, text)
    
    return text, tokens

def restore_math(text, tokens):
    """Restore math blocks from tokens with smart spacing"""
    for i, token in enumerate(tokens):
        placeholder = f"__MATH_TOKEN_{i}__"
        
        idx = text.find(placeholder)
        if idx == -1:
            # Fallback if somehow missing
            text = text.replace(placeholder, token)
            continue
            
        prefix = ""
        # Check char before: if alnum or closing punctuation, add space
        if idx > 0:
            c = text[idx-1]
            if (c.isalnum() or c in ')}],.') and not c.isspace():
                prefix = " "
                
        suffix = ""
        # Check char after: if alnum (start of word), add space
        end_idx = idx + len(placeholder)
        if end_idx < len(text):
            c = text[end_idx]
            if c.isalnum() and not c.isspace():
                suffix = " "
        
        replacement = prefix + token + suffix
        text = text.replace(placeholder, replacement)
                 
    return text

def clean_math(text):
    """Clean up math mode transitions"""
    # Clean inner spacing for math blocks: $ H $ -> $H$
    # Matches $ (optional_space) (content) (optional_space) $
    # Content allows escaped chars or non-$
    text = re.sub(r'(?<!\\)\$(\s+)?((?:\\.|[^$])+?)(\s+)?\$(?!\d)', r'$\2$', text)
    return text

def migrate_note(obsidian_path, output_dir, tags=None, dry_run=False, force=False):
    """Migrate a single note"""
    try:
        gwiki_content, title = convert_to_gwiki(obsidian_path, tags)

        # Create output filename
        output_filename = title + '.tex'
        output_path = Path(output_dir) / output_filename

        if output_path.exists() and not force:
            print(f"• Skipped: {obsidian_path} -> {output_path} (file exists)")
            return output_path

        if dry_run:
            print(f"\n{'='*80}")
            print(f"Would create: {output_path}")
            print(f"{'='*80}")
            print(gwiki_content[:500] + '...' if len(gwiki_content) > 500 else gwiki_content)
            return output_path
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(gwiki_content)
            print(f"✓ Migrated: {obsidian_path} -> {output_path}")

            # Build PDF and HTML
            print(f"  Building PDF...")
            build_pdf = subprocess.run(["bash", "scripts/build-note.sh", str(output_path), "build"], capture_output=True)
            if build_pdf.returncode == 0:
                 # Move result
                 pdf_name = output_path.stem + ".pdf"
                 built_pdf = Path("build") / pdf_name
                 final_pdf = Path("pdfs") / pdf_name
                 # Ensure pdfs dir exists
                 Path("pdfs").mkdir(exist_ok=True)
                 if built_pdf.exists():
                     os.rename(built_pdf, final_pdf)
                     print(f"  ✓ PDF built: pdfs/{pdf_name}")
            else:
                 print(f"  ✗ PDF build failed")

            print(f"  Building HTML...")
            html_name = output_path.stem + ".html"
            html_path = Path("html") / html_name
            # Ensure html dir exists
            Path("html").mkdir(exist_ok=True)
            
            build_html = subprocess.run(["python3", "scripts/tex-to-html.py", str(output_path), str(html_path)], capture_output=True)
            if build_html.returncode == 0:
                 print(f"  ✓ HTML built: html/{html_name}")
            else:
                 print(f"  ✗ HTML build failed: {build_html.stderr.decode()[:200]}...")

            return output_path

    except Exception as e:
        print(f"✗ Error migrating {obsidian_path}: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate Obsidian notes to GWiki format')
    parser.add_argument('input', help='Obsidian note file(s) to migrate', nargs='+')
    parser.add_argument('-o', '--output', default='notes', help='Output directory (default: notes)')
    parser.add_argument('-t', '--tags', help='Tags to add (comma-separated)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing files')

    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite existing files')

    args = parser.parse_args()

    tags = args.tags.split(',') if args.tags else None

    for input_path in args.input:
        migrate_note(input_path, args.output, tags, args.dry_run, args.force)
