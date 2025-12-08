#!/bin/bash
# GWiki - Create New Article
# Usage: ./new-article.sh <article-id> "<title>"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ARTICLES_DIR="$ROOT_DIR/articles"
TEMPLATES_DIR="$ROOT_DIR/templates"

ID="$1"
TITLE="$2"
DATE=$(date +"%Y-%m-%d")

if [ -z "$ID" ] || [ -z "$TITLE" ]; then
    echo "Usage: $0 <article-id> \"<title>\""
    echo "Example: $0 cat-theory-intro \"Introduction to Category Theory\""
    exit 1
fi

OUTPUT_FILE="$ARTICLES_DIR/$ID.tex"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Error: Article '$ID' already exists at $OUTPUT_FILE"
    exit 1
fi

cat > "$OUTPUT_FILE" << EOF
\\documentclass[type=article,gwikiid=$ID]{gwiki}

%% ============================================================================
%% $TITLE
%% GWiki Article - Created $DATE
%% ============================================================================

\\GWikiMeta{$ID}{$TITLE}{article}[math, physics]
\\GWikiAuthor{Author Name}
\\GWikiDate{$DATE}
\\GWikiSummary{%
  A brief summary of this article goes here.
}

\\begin{document}

\\gwikiarticleheader

%% Prerequisites (uncomment and customize if needed)
%% \\prerequisites{prerequisite-id-1, prerequisite-id-2}

\\tableofcontents

%% ============================================================================
\\section{Introduction}
%% ============================================================================

This is the introduction to $TITLE.

%% Reference other wiki notes like this:
%% \\wref{wiki-note-id}[optional display text]

%% Reference other articles like this:
%% \\articleref{article-id}[optional display text]

%% ============================================================================
\\section{Main Content}
%% ============================================================================

\\begin{definition}[Important Definition]
  A \\concept{key concept} is defined as follows...
\\end{definition}

\\begin{theorem}[Main Theorem]
  The main result states that...
\\end{theorem}

\\begin{proof}
  The proof proceeds as follows...
\\end{proof}

%% TikZ diagrams work seamlessly:
\\begin{center}
\\begin{tikzpicture}
  \\node (A) at (0,0) {\$A\$};
  \\node (B) at (2,0) {\$B\$};
  \\draw[->] (A) -- node[above] {\$f\$} (B);
\\end{tikzpicture}
\\end{center}

%% ============================================================================
\\section{Examples}
%% ============================================================================

\\begin{example}
  Here is an illustrative example...
\\end{example}

%% ============================================================================
\\section{Conclusion}
%% ============================================================================

Summary of the article.

%% Related topics
\\seealso{related-topic-1, related-topic-2}

\\gwikifooter

\\end{document}
EOF

echo "Created new article: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit $OUTPUT_FILE to add your content"
echo "  2. Run 'make article ID=$ID' to build the PDF"
echo "  3. Run 'make index' to update the index"
