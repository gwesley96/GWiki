#!/bin/bash
# Double-click this file to build everything (PDFs + Web)

cd "$(dirname "$0")"

echo "════════════════════════════════════════"
echo "  GWiki: Building Everything"
echo "════════════════════════════════════════"
echo ""

# Build PDFs
echo "📄 Building PDFs..."
make all

echo ""
echo "🌐 Building web version..."
make html

echo ""
echo "📑 Generating indices..."
make indices

echo ""
echo "════════════════════════════════════════"
echo "  ✅ BUILD COMPLETE!"
echo "════════════════════════════════════════"
echo ""
echo "Output:"
echo "  • PDFs:  pdfs/"
echo "  • HTML:  html/"
echo "  • Index: index.html"
echo ""
echo "Press any key to open web index..."
read -n 1 -s

open index.html
