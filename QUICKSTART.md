# GWiki Quick Start

## Setup (One Time)

1. **Open in VS Code:**
   ```bash
   cd GWiki
   code .
   ```

2. **Install the GWiki extension** (for autocomplete):
   - Open VS Code
   - Go to Extensions (Cmd+Shift+X)
   - Click "..." → "Install from VSIX..."
   - Navigate to `.vscode/gwiki-extension/` and install

   Or just use the snippets (they work automatically).

## Daily Workflow

### Create a New Note

```bash
make new NAME=my-topic TITLE="My Topic"
```

This creates `notes/my-topic.tex`:

```latex
\documentclass{gwiki}

\Title{My Topic}
\Tags{}

\begin{document}

\NoteHeader

%% Your content here...

\end{document}
```

That's it. No IDs to manage. The filename IS the ID.

### Write Content

```latex
\documentclass{gwiki}

\Title{Functor}
\Tags{category-theory}

\begin{document}

\NoteHeader

\begin{definition}
A \textbf{functor} $F : \cC \to \cD$ maps objects and morphisms...
\end{definition}

%% Link to another note - just use the filename!
See also \wref{category} for the definition of category.

%% Link with custom text
This is related to \wref{natural-transformation}[natural transformations].

\end{document}
```

### Build

```bash
make                 # Build all notes
make functor         # Build just functor.tex
make watch           # Auto-rebuild on save
```

PDFs go to `build/pdf/`.

## Linking

**One command: `\wref{}`** - Links between PDFs work! Click a link to open the other PDF.

| What you write | What it does |
|----------------|--------------|
| `\wref{functor}` | Links to functor.pdf, shows "functor" |
| `\wref{functor}[Functors]` | Links to functor.pdf, shows "Functors" |
| `\wref{#sec:examples}` | Links to label in same file |
| `\wref{functor#thm:main}` | Links to functor.pdf at specific section |

**Note:** Cross-PDF links work in most PDF viewers (Preview, Adobe, Okular, etc.). Keep all PDFs in the same `build/pdf/` directory for relative links to work.

## Autocomplete

When you type `\wref{`, VS Code shows suggestions:
- Sorted by most recently edited
- Shows title, not filename
- Just click to insert

Run `make completions` to refresh the list.

## Your Math Macros

All your macros work:
- `\bR`, `\bC`, `\bZ` (blackboard bold)
- `\cC`, `\cD` (calligraphic)
- `\a`, `\b`, `\g` (Greek)
- `\Set`, `\Grp`, `\Top` (categories)
- `\to`, `\incto`, `\sjto` (arrows)
- All TikZ and tikz-cd diagrams

## Example: Complete Note

```latex
\documentclass{gwiki}

\Title{Yoneda Lemma}
\Tags{category-theory, representable}

\begin{document}

\NoteHeader

\prereq{functor, natural-transformation}

\begin{theorem}[Yoneda]
For $F : \cC \to \Set$ and $A \in \cC$:
\[
  \Nat(\yo_A, F) \cong F(A)
\]
naturally in $A$ and $F$.
\end{theorem}

\begin{proof}
Given $\a : \yo_A \to F$, take $\a_A(\id_A) \in F(A)$...
\end{proof}

\begin{tikzcd}
  \yo_A \ar[r, "\a"] & F
\end{tikzcd}

\seealso{representable-functor, presheaf}

\end{document}
```

## File Structure

```
GWiki/
├── notes/           ← Your notes go here
│   ├── category.tex
│   ├── functor.tex
│   └── ...
├── lib/             ← LaTeX packages (don't edit)
├── build/pdf/       ← Output PDFs
└── Makefile
```

## Commands Summary

| Command | What it does |
|---------|--------------|
| `make new NAME=x` | Create new note |
| `make` | Build all |
| `make x` | Build notes/x.tex |
| `make watch` | Auto-rebuild |
| `make clean` | Delete build files |
