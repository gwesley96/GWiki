#!/bin/bash
# Double-click this file to create a new note with a GUI dialog

cd "$(dirname "$0")"

# Use AppleScript to get note title and tags
TITLE=$(osascript -e 'Tell application "System Events" to display dialog "Enter note title:" default answer "" with title "Create New Note"' -e 'text returned of result' 2>/dev/null)

if [ -z "$TITLE" ]; then
    echo "Cancelled"
    exit 0
fi

TAGS=$(osascript -e 'Tell application "System Events" to display dialog "Enter tags (comma-separated, or leave empty):" default answer "" with title "Create New Note"' -e 'text returned of result' 2>/dev/null)

# Create the note
./scripts/new-note.sh "$TITLE" "$TAGS"

# Ask if user wants to open it
osascript -e "Tell application \"System Events\" to display dialog \"Note created: notes/$TITLE.tex\n\nOpen in editor?\" buttons {\"No\", \"Yes\"} default button \"Yes\"" -e 'button returned of result' > /tmp/response.txt 2>/dev/null

if grep -q "Yes" /tmp/response.txt 2>/dev/null; then
    # Open in default text editor
    open "notes/$TITLE.tex"
fi

rm -f /tmp/response.txt
