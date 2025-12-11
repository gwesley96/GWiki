#!/usr/bin/env python3
"""
Obsidian to GWiki Migration Script
Converts Obsidian markdown notes to GWiki LaTeX format
"""

import re
import sys
import os
from pathlib import Path
from datetime import datetime

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

def convert_wikilinks(text):
    """Convert Obsidian [[wikilinks]] to GWiki \wref{}"""
    # [[link|display]] -> \wref[display]{link}
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\\wref[\2]{\1}', text)
    # [[link]] -> \wref{link}
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\\wref{\1}', text)
    return text

def convert_hashtags(text):
    """Convert #tags to comments or remove them"""
    # Remove common workflow tags
    text = re.sub(r'#(todo|unfinished|organize-this|article)\s*', '', text)
    # Keep other tags as comments
    text = re.sub(r'#(\w+)', r'% Tag: \1', text)
    return text

def convert_images(text):
    """Handle ![[image.png]] embeds"""
    # Convert to comments since GWiki doesn't have direct image support
    text = re.sub(r'!\[\[([^\]]+)\]\]', r'% Image: \1 (not migrated)', text)
    return text

def clean_math(text):
    """Clean up math mode transitions"""
    # Ensure proper spacing around inline math
    text = re.sub(r'([a-zA-Z])\$', r'\1 $', text)
    text = re.sub(r'\$([a-zA-Z])', r'$ \1', text)
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

    # Convert body
    body = convert_wikilinks(body)
    body = convert_hashtags(body)
    body = convert_images(body)
    body = clean_math(body)
    body = body.strip()

    # Build GWiki document
    gwiki_content = r'\documentclass{gwiki}' + '\n\n'
    gwiki_content += f'\\Title{{{title}}}' + '\n'

    if tags:
        gwiki_content += f'\\Tags{{{", ".join(tags)}}}' + '\n'
    else:
        gwiki_content += '\\Tags{}' + '\n'

    gwiki_content += '\n\\begin{document}\n\n'
    gwiki_content += '\\NoteHeader\n\n'

    # Add body
    gwiki_content += body + '\n\n'

    gwiki_content += '\\References\n\n'
    gwiki_content += '\\Footer\n\n'
    gwiki_content += '\\end{document}\n'

    return gwiki_content, title

def migrate_note(obsidian_path, output_dir, tags=None, dry_run=False):
    """Migrate a single note"""
    try:
        gwiki_content, title = convert_to_gwiki(obsidian_path, tags)

        # Create output filename
        output_filename = title + '.tex'
        output_path = Path(output_dir) / output_filename

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

    args = parser.parse_args()

    tags = args.tags.split(',') if args.tags else None

    for input_path in args.input:
        migrate_note(input_path, args.output, tags, args.dry_run)
