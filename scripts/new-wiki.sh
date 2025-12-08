#!/bin/bash
# GWiki - Create New Wiki Note
# Usage: ./new-wiki.sh <note-id> "<title>"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
WIKI_DIR="$ROOT_DIR/wiki"
TEMPLATES_DIR="$ROOT_DIR/templates"

ID="$1"
TITLE="$2"
DATE=$(date +"%Y-%m-%d")

if [ -z "$ID" ] || [ -z "$TITLE" ]; then
    echo "Usage: $0 <note-id> \"<title>\""
    echo "Example: $0 functor \"Functor\""
    exit 1
fi

OUTPUT_FILE="$WIKI_DIR/$ID.tex"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Error: Wiki note '$ID' already exists at $OUTPUT_FILE"
    exit 1
fi

cat > "$OUTPUT_FILE" << EOF
\\documentclass[type=wiki,gwikiid=$ID]{gwiki}

%% ============================================================================
%% $TITLE
%% GWiki Note - Created $DATE
%% ============================================================================

\\GWikiMeta{$ID}{$TITLE}{wiki}[definition, math]
\\GWikiDate{$DATE}
\\GWikiSummary{%
  Brief one-line description of $TITLE.
}

\\begin{document}

\\gwikinoteheader

%% ============================================================================
%% Definition
%% ============================================================================

\\begin{definition}[$TITLE]
  A \\concept{$TITLE} is defined as...
\\end{definition}

%% ============================================================================
%% Properties
%% ============================================================================

Key properties:
\\begin{lst}
  \\item First property
  \\item Second property
\\end{lst}

%% ============================================================================
%% Examples
%% ============================================================================

\\begin{example}
  A standard example is...
\\end{example}

%% ============================================================================
%% Related Concepts
%% ============================================================================

\\seealso{related-concept-1, related-concept-2}

\\gwikifooter

\\end{document}
EOF

echo "Created new wiki note: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit $OUTPUT_FILE to add your content"
echo "  2. Run 'make wiki ID=$ID' to build the PDF"
echo "  3. Run 'make index' to update the index"
