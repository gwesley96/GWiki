#!/bin/bash
# Double-click this file to open the web index in your browser

cd "$(dirname "$0")"

# Check if index.html exists, if not generate it
if [ ! -f "index.html" ]; then
    echo "Generating web index..."
    make indices > /dev/null 2>&1
fi

# Open in default browser
open index.html

echo "✓ Opened web index in browser"
echo "  You can now search and browse all your notes!"
sleep 2
