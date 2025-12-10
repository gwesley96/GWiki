#!/bin/bash
# Build a single note with creation date injected

NOTE_FILE="$1"
BUILD_DIR="$2"

if [ -z "$NOTE_FILE" ] || [ -z "$BUILD_DIR" ]; then
    echo "Usage: build-note.sh <note.tex> <build-dir>"
    exit 1
fi

NOTE_NAME=$(basename "$NOTE_FILE" .tex)

# Get creation date from metadata
CREATED_DATE=$(python3 -c "
import json, sys
from pathlib import Path
try:
    data = json.loads(Path('.gwiki-metadata.json').read_text())
    print(data.get('creation_dates', {}).get('$NOTE_NAME', ''))
except:
    print('')
")

# Build with creation date if available
if [ -n "$CREATED_DATE" ]; then
    # Create temp file with creation date injected
    TEMP_FILE=$(mktemp)
    echo "\\def\\gwikicreateddate{$CREATED_DATE}" > "$TEMP_FILE"
    echo "\\input{$NOTE_FILE}" >> "$TEMP_FILE"

    TEXINPUTS=lib: pdflatex -jobname="$NOTE_NAME" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" "$TEMP_FILE" > /dev/null 2>&1
    TEXINPUTS=lib: pdflatex -jobname="$NOTE_NAME" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" "$TEMP_FILE" > /dev/null 2>&1

    rm "$TEMP_FILE"
else
    # No creation date, build normally
    TEXINPUTS=lib: pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" "$NOTE_FILE" > /dev/null 2>&1
    TEXINPUTS=lib: pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" "$NOTE_FILE" > /dev/null 2>&1
fi
