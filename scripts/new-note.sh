#!/bin/bash
# Quick note creation script for GWiki
# Usage: ./scripts/new-note.sh "note title" ["tag1, tag2, ..."]

set -e

NOTES_DIR="notes"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

if [ -z "$1" ]; then
    echo "Usage: $0 \"note title\" [\"tag1, tag2, ...\"]"
    echo ""
    echo "Examples:"
    echo "  $0 \"Banach space\""
    echo "  $0 \"Green function\" \"analysis, differential-equations\""
    echo "  $0 \"a cohomology theory\" \"algebraic-topology, homotopy-theory\""
    exit 1
fi

TITLE="$1"
TAGS="${2:-}"

# Create filename from title (lowercase, spaces to spaces, no special chars)
FILENAME=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]')

# Check if file exists
FILEPATH="$NOTES_DIR/$FILENAME.tex"
if [ -f "$FILEPATH" ]; then
    echo "Error: $FILEPATH already exists"
    exit 1
fi

# Create the note
mkdir -p "$NOTES_DIR"

cat > "$FILEPATH" <<EOF
\documentclass{gwiki}
\usepackage{gwiki-links}

\Title{$TITLE}
\Tags{$TAGS}

\begin{document}
\NoteHeader

%% Write your note here...


\end{document}
EOF

# Track creation date
python3 scripts/track-creation-dates.py > /dev/null 2>&1

echo "✓ Created: $FILEPATH"
echo ""
echo "Next steps:"
echo "  1. Edit $FILEPATH"
echo "  2. make         # Build PDF"
echo "  3. make web     # Build HTML version"

# Open in editor if EDITOR is set
if [ -n "$EDITOR" ]; then
    echo ""
    echo "Opening in $EDITOR..."
    $EDITOR "$FILEPATH"
fi
