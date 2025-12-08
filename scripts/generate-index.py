#!/usr/bin/env python3
"""
GWiki Index Generator

Scans all articles and wiki notes, extracts metadata, and generates:
1. JSON index files for programmatic access
2. Cross-reference database for backlinks
3. Tag-based categorization
4. Dependency graph data

Usage: python3 generate-index.py
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
ROOT_DIR = Path(__file__).parent.parent
ARTICLES_DIR = ROOT_DIR / "articles"
WIKI_DIR = ROOT_DIR / "wiki"
INDEX_DIR = ROOT_DIR / "index"
BUILD_DIR = ROOT_DIR / "build"

# Ensure directories exist
INDEX_DIR.mkdir(exist_ok=True)

def extract_metadata(tex_file):
    """Extract GWiki metadata from a .tex file."""
    metadata = {
        'id': '',
        'title': '',
        'type': '',
        'tags': [],
        'date': '',
        'author': '',
        'summary': '',
        'prerequisites': [],
        'references': [],  # outgoing links
        'file': str(tex_file),
    }

    try:
        content = tex_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {tex_file}: {e}")
        return metadata

    # Extract GWikiID
    match = re.search(r'\\GWikiID\{([^}]+)\}', content)
    if match:
        metadata['id'] = match.group(1)

    # Extract from GWikiMeta (combined command)
    match = re.search(r'\\GWikiMeta\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}(?:\[([^\]]*)\])?', content)
    if match:
        metadata['id'] = match.group(1)
        metadata['title'] = match.group(2)
        metadata['type'] = match.group(3)
        if match.group(4):
            metadata['tags'] = [t.strip() for t in match.group(4).split(',')]

    # Extract individual fields if not set by GWikiMeta
    if not metadata['title']:
        match = re.search(r'\\GWikiTitle\{([^}]+)\}', content)
        if match:
            metadata['title'] = match.group(1)

    if not metadata['type']:
        match = re.search(r'\\GWikiType\{([^}]+)\}', content)
        if match:
            metadata['type'] = match.group(1)

    if not metadata['tags']:
        match = re.search(r'\\GWikiTags\{([^}]+)\}', content)
        if match:
            metadata['tags'] = [t.strip() for t in match.group(1).split(',')]

    match = re.search(r'\\GWikiDate\{([^}]+)\}', content)
    if match:
        metadata['date'] = match.group(1)

    match = re.search(r'\\GWikiAuthor\{([^}]+)\}', content)
    if match:
        metadata['author'] = match.group(1)

    match = re.search(r'\\GWikiSummary\{([^}]+)\}', content, re.DOTALL)
    if match:
        metadata['summary'] = ' '.join(match.group(1).split())

    # Extract prerequisites
    match = re.search(r'\\GWikiPrereqs\{([^}]+)\}', content)
    if match:
        metadata['prerequisites'] = [p.strip() for p in match.group(1).split(',')]

    match = re.search(r'\\prerequisites\{([^}]+)\}', content)
    if match:
        metadata['prerequisites'] = [p.strip() for p in match.group(1).split(',')]

    # Extract all references (wref, wikiref, articleref)
    refs = set()
    for pattern in [r'\\wref\{([^}]+)\}', r'\\wikiref\{([^}]+)\}', r'\\articleref\{([^}]+)\}']:
        for match in re.finditer(pattern, content):
            refs.add(match.group(1))

    metadata['references'] = list(refs)

    return metadata

def scan_directory(directory, doc_type):
    """Scan a directory for .tex files and extract metadata."""
    documents = {}

    if not directory.exists():
        return documents

    for tex_file in directory.glob("*.tex"):
        metadata = extract_metadata(tex_file)

        # Use filename as ID if not specified
        if not metadata['id']:
            metadata['id'] = tex_file.stem

        # Set type if not specified
        if not metadata['type']:
            metadata['type'] = doc_type

        documents[metadata['id']] = metadata

    return documents

def build_backlinks(all_docs):
    """Build backlink index from forward references."""
    backlinks = defaultdict(list)

    for doc_id, metadata in all_docs.items():
        for ref in metadata.get('references', []):
            if ref != doc_id:  # Don't include self-references
                backlinks[ref].append(doc_id)

    return dict(backlinks)

def build_tag_index(all_docs):
    """Build index of documents by tag."""
    tag_index = defaultdict(list)

    for doc_id, metadata in all_docs.items():
        for tag in metadata.get('tags', []):
            tag_index[tag].append(doc_id)

    return dict(tag_index)

def generate_graph_data(all_docs, backlinks):
    """Generate data for dependency graph visualization."""
    nodes = []
    edges = []

    for doc_id, metadata in all_docs.items():
        nodes.append({
            'id': doc_id,
            'title': metadata.get('title', doc_id),
            'type': metadata.get('type', 'unknown'),
            'tags': metadata.get('tags', []),
        })

        for ref in metadata.get('references', []):
            if ref in all_docs:
                edges.append({
                    'source': doc_id,
                    'target': ref,
                })

    return {'nodes': nodes, 'edges': edges}

def main():
    print("GWiki Index Generator")
    print("=" * 40)

    # Scan all documents
    print("\nScanning articles...")
    articles = scan_directory(ARTICLES_DIR, 'article')
    print(f"  Found {len(articles)} articles")

    print("Scanning wiki notes...")
    wiki_notes = scan_directory(WIKI_DIR, 'wiki')
    print(f"  Found {len(wiki_notes)} wiki notes")

    # Combine all documents
    all_docs = {**articles, **wiki_notes}
    print(f"\nTotal documents: {len(all_docs)}")

    # Build indexes
    print("\nBuilding indexes...")
    backlinks = build_backlinks(all_docs)
    tag_index = build_tag_index(all_docs)
    graph_data = generate_graph_data(all_docs, backlinks)

    # Add backlinks to document metadata
    for doc_id in all_docs:
        all_docs[doc_id]['backlinks'] = backlinks.get(doc_id, [])

    # Generate index files
    print("Writing index files...")

    # Main index
    index_data = {
        'generated': datetime.now().isoformat(),
        'stats': {
            'total': len(all_docs),
            'articles': len(articles),
            'wiki_notes': len(wiki_notes),
            'tags': len(tag_index),
        },
        'documents': all_docs,
    }

    with open(INDEX_DIR / 'index.json', 'w') as f:
        json.dump(index_data, f, indent=2)
    print(f"  → {INDEX_DIR / 'index.json'}")

    # Articles index
    with open(INDEX_DIR / 'articles.json', 'w') as f:
        json.dump(articles, f, indent=2)
    print(f"  → {INDEX_DIR / 'articles.json'}")

    # Wiki notes index
    with open(INDEX_DIR / 'wiki.json', 'w') as f:
        json.dump(wiki_notes, f, indent=2)
    print(f"  → {INDEX_DIR / 'wiki.json'}")

    # Backlinks index
    with open(INDEX_DIR / 'backlinks.json', 'w') as f:
        json.dump(backlinks, f, indent=2)
    print(f"  → {INDEX_DIR / 'backlinks.json'}")

    # Tag index
    with open(INDEX_DIR / 'tags.json', 'w') as f:
        json.dump(tag_index, f, indent=2)
    print(f"  → {INDEX_DIR / 'tags.json'}")

    # Graph data
    with open(INDEX_DIR / 'graph.json', 'w') as f:
        json.dump(graph_data, f, indent=2)
    print(f"  → {INDEX_DIR / 'graph.json'}")

    # Summary
    print("\n" + "=" * 40)
    print("Index generation complete!")
    print(f"\nTags found: {', '.join(sorted(tag_index.keys())) or '(none)'}")

    if backlinks:
        most_linked = max(backlinks.keys(), key=lambda k: len(backlinks[k]))
        print(f"Most referenced: {most_linked} ({len(backlinks[most_linked])} backlinks)")

if __name__ == '__main__':
    main()
