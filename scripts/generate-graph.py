#!/usr/bin/env python3
"""
GWiki Graph Generator

Generates an SVG visualization of the document dependency graph.
Requires: graphviz (pip install graphviz)

Usage: python3 generate-graph.py
"""

import json
from pathlib import Path

try:
    from graphviz import Digraph
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

ROOT_DIR = Path(__file__).parent.parent
INDEX_DIR = ROOT_DIR / "index"
BUILD_DIR = ROOT_DIR / "build"

# Color scheme for different document types
TYPE_COLORS = {
    'article': '#4A90D9',    # Blue
    'wiki': '#7CB342',       # Green
    'unknown': '#9E9E9E',    # Gray
}

def generate_graph():
    """Generate SVG graph from index data."""

    # Load graph data
    graph_file = INDEX_DIR / 'graph.json'
    if not graph_file.exists():
        print("Error: graph.json not found. Run 'make index' first.")
        return False

    with open(graph_file) as f:
        data = json.load(f)

    if not HAS_GRAPHVIZ:
        print("Warning: graphviz package not installed.")
        print("Install with: pip install graphviz")
        print("\nGenerating DOT file instead...")

        # Generate DOT file manually
        dot_content = ['digraph GWiki {']
        dot_content.append('  rankdir=LR;')
        dot_content.append('  node [shape=box, style=filled];')

        for node in data['nodes']:
            color = TYPE_COLORS.get(node['type'], TYPE_COLORS['unknown'])
            label = node['title'][:30] + '...' if len(node['title']) > 30 else node['title']
            dot_content.append(f'  "{node["id"]}" [label="{label}", fillcolor="{color}"];')

        for edge in data['edges']:
            dot_content.append(f'  "{edge["source"]}" -> "{edge["target"]}";')

        dot_content.append('}')

        BUILD_DIR.mkdir(exist_ok=True)
        dot_file = BUILD_DIR / 'graph.dot'
        with open(dot_file, 'w') as f:
            f.write('\n'.join(dot_content))

        print(f"DOT file written to: {dot_file}")
        print("Convert to SVG with: dot -Tsvg graph.dot -o graph.svg")
        return True

    # Create graph with graphviz
    dot = Digraph(comment='GWiki Document Graph')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='filled')

    # Add nodes
    for node in data['nodes']:
        color = TYPE_COLORS.get(node['type'], TYPE_COLORS['unknown'])
        label = node['title'][:30] + '...' if len(node['title']) > 30 else node['title']
        dot.node(node['id'], label=label, fillcolor=color)

    # Add edges
    for edge in data['edges']:
        dot.edge(edge['source'], edge['target'])

    # Render
    BUILD_DIR.mkdir(exist_ok=True)
    output_path = BUILD_DIR / 'graph'
    dot.render(output_path, format='svg', cleanup=True)

    print(f"Graph generated: {output_path}.svg")
    return True

def main():
    print("GWiki Graph Generator")
    print("=" * 40)
    generate_graph()

if __name__ == '__main__':
    main()
