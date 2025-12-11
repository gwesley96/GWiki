# GWiki

A modern LaTeX-based mathematical knowledge base with automatic organization, web publishing, and smart indexing.

## Quick Start

**Create a new note:**
```bash
./scripts/new-note.sh "Banach space" "functional-analysis, topology"
```

**Build everything:**
```bash
make vault      # PDFs, validation, bibliography, indices
make web        # HTML version with master index
```

**Output:**
- `pdfs/` - PDF notes
- `html/` - HTML notes (with MathJax & TikZJax)
- `index.html` - Beautiful web index with search
- `indices/` - LaTeX indices (alphabetical, by-tag, chronological)

## Note Format

```latex
\documentclass{gwiki}

\Title{note title}
\Tags{tag1, tag2}
\Topics{Topics covered in this note.}

\begin{document}

\KeySources{\nlab{page}, \arxiv{1234.56789}}
\NoteHeader

\begin{idea}
Main conceptual point.
\end{idea}

Content here.

\SeeAlso{related notes}

\end{document}
```

## Features

### PDF System
- **Automatic dates**: Created = file birth time, Modified = file mtime
- **Clean headers**: Title, key sources, tags, dates - all automatic
- **Compact idea boxes**: Inline "**Idea.**" title saves space
- **Smart formatting**: Empty tags hidden, metadata in monospace
- **Website in footer**: Links to greysonwesley.com

### Web Publishing
- **Master index**: Beautiful HTML landing page with search and filters
- **Tag organization**: Notes automatically grouped by tags
- **Recent notes**: Chronological view of latest additions
- **Interactive search**: Real-time filtering by title, tags, or content
- **Table of contents**: Auto-generated for notes with 3+ sections
- **Backlinks**: Bidirectional linking shows all references
- **MathJax + TikZJax**: Full LaTeX math and diagrams in browser

### Organization
- **Master indices**: Alphabetical, by-tag, and chronological views (LaTeX + HTML)
- **Auto-bibliography**: Fetches BibTeX from arXiv/DOI automatically
- **Link validation**: Compact error reporting with line numbers
- **Metadata tracking**: Persistent creation dates and link graphs

## Links

```latex
\wref{other note}              % Link to note (not italicized)
\wref[custom]{note}            % Custom display text
\SeeAlso{note1, note2}         % Related notes
```

## Citations

```latex
\arxiv{1234.56789}             % Auto-fetch from arXiv
\nlab{page}                    % Auto-generate entry
```

## Commands

### Common
```bash
make              # Build all PDFs → pdfs/
make vault        # Build everything: validate, bibliography, indices
make web          # Build web version: HTML notes + master index
make new NAME="note title"   # Create new note (deprecated, use script below)
make clean        # Remove all build artifacts
```

### Specialized
```bash
make html         # Convert notes to HTML
make indices      # Generate master indices (HTML + LaTeX)
make validate     # Check for broken links
make bibliography # Generate bibliography from arXiv/DOI citations
```

### Scripts
```bash
./scripts/new-note.sh "note title" "tag1, tag2"   # Create new note (recommended)
python3 scripts/generate-master-index.py          # Regenerate indices
python3 scripts/tex-to-html.py notes/file.tex     # Convert single note
```

## File Naming

Use spaces: `Green function.tex` ✓
Not hyphens: `Green-function.tex` ✗
Capitalize proper nouns only
