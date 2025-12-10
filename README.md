# GWiki

Mathematical note system with automatic dates and clean formatting.

## Quick Start

```bash
make new NAME="note title"
vim "notes/note title.tex"
make
```

PDFs in `pdfs/`, build artifacts in `build/`

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

- **Automatic dates**: Created = file birth time, Modified = file mtime
- **Clean headers**: Title, key sources, tags, dates - all automatic
- **Compact idea boxes**: Inline "**Idea.**" title saves space
- **Smart formatting**: Empty tags hidden, metadata in monospace
- **Website in footer**: Links to greysonwesley.com

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

```bash
make              # Build all → pdfs/
make validate     # Check links (compact)
make clean        # Remove builds
```

## File Naming

Use spaces: `Green function.tex` ✓
Not hyphens: `Green-function.tex` ✗
Capitalize proper nouns only
