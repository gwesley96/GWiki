# GWiki

**A LaTeX-based interconnected note system combining the best of Obsidian, cphysics.org, and nLab.**

GWiki lets you write mathematical notes and articles with the full power of LaTeX (including TikZ), while enjoying the interconnectedness and ease of wiki-style linking found in tools like Obsidian. It supports both PDF and HTML output (via LWarp).

## Features

- **Full LaTeX Power**: Use all LaTeX features including TikZ/PGF diagrams, theorem environments, and custom macros
- **Interconnected Notes**: Wiki-style linking between documents with unique IDs
- **Two Document Types**:
  - **Articles**: Longer, self-contained expositions (like cphysics.org)
  - **Wiki Notes**: Shorter, definition-focused entries (like nLab)
- **Automatic Backlinks**: Track which documents reference each other
- **HTML Output**: Generate web-ready HTML with MathJax and SVG diagrams via LWarp
- **Automated Build System**: One command to build everything
- **Rich Theorem Environments**: Theorems, lemmas, definitions, examples, and more with consistent styling
- **Tagging System**: Organize notes by topic with tags
- **Dependency Graph**: Visualize connections between documents

## Quick Start

### 1. Create a New Article

```bash
make new-article ID=my-first-article TITLE="My First Article"
```

This creates `articles/my-first-article.tex` from a template.

### 2. Create a New Wiki Note

```bash
make new-wiki ID=important-concept TITLE="Important Concept"
```

This creates `wiki/important-concept.tex` from a template.

### 3. Build PDFs

```bash
# Build all PDFs
make pdf

# Build a single article
make article ID=my-first-article

# Build a single wiki note
make wiki ID=important-concept
```

### 4. Build HTML (requires LWarp)

```bash
make html
```

### 5. Generate Index

```bash
make index
```

## Directory Structure

```
GWiki/
├── articles/          # Long-form articles (cphysics-style)
├── wiki/              # Short wiki notes (nLab-style)
├── lib/               # LaTeX classes and packages
│   ├── gwiki.cls      # Main document class
│   ├── gwiki-macros.sty   # Math macros
│   ├── gwiki-links.sty    # Linking system
│   ├── gwiki-lwarp.sty    # LWarp integration
│   └── tz.sty         # TikZ extensions
├── build/             # Build output
│   ├── pdf/           # PDF files
│   └── html/          # HTML files
├── index/             # Generated index files (JSON)
├── scripts/           # Build automation scripts
├── assets/            # CSS, JS, images
├── templates/         # Document templates
└── Makefile           # Build system
```

## Linking Between Documents

### Basic Links

```latex
% Link to another document
\wref{document-id}

% Link with custom display text
\wref{document-id}[Custom Text]

% Link specifically to wiki notes
\wikiref{wiki-note-id}

% Link specifically to articles
\articleref{article-id}
```

### Prerequisites

```latex
% List prerequisites at the start of a document
\prerequisites{prereq-1, prereq-2, prereq-3}
```

### Related Topics

```latex
% At the end of a document
\seealso{related-1, related-2, related-3}
```

### Section Links

```latex
% Create a linkable section
\wsection{Section Title}{section-id}

% Reference a section in another document
\wsecref{document-id}{section-id}
```

## Document Metadata

Every GWiki document should declare its metadata:

```latex
\documentclass[type=article,gwikiid=unique-id]{gwiki}

\GWikiMeta{unique-id}{Document Title}{article}[tag1, tag2]
\GWikiAuthor{Your Name}
\GWikiDate{2025-12-08}
\GWikiSummary{Brief description of the document.}

\begin{document}
\gwikiarticleheader  % For articles
% OR
\gwikinoteheader     % For wiki notes

% ... content ...

\gwikifooter
\end{document}
```

## Math Macros

GWiki includes a comprehensive set of math macros:

### Alphabet Shortcuts

| Prefix | Style | Example |
|--------|-------|---------|
| `\b` | Blackboard bold | `\bR` → ℝ |
| `\c` | Calligraphic | `\cC` → 𝒞 |
| `\f` | Fraktur | `\fG` → 𝔊 |
| `\s` | Script | `\sH` → ℋ |
| `\t` | Bold | `\tA` → **A** |

### Greek Shortcuts

- `\a` → α, `\b` → β, `\g` → γ, `\d` → δ, `\e` → ε
- `\G` → Γ, `\D` → Δ, `\L` → Λ, `\S` → Σ, `\O` → Ω

### Operators

- Categories: `\Set`, `\Grp`, `\Top`, `\Vec`, `\Cat`, `\Fun`
- Operations: `\Hom`, `\End`, `\Aut`, `\Ext`, `\Tor`, `\colim`

### Arrows

- `\to`, `\lto`, `\incto` (↪), `\sjto` (↠), `\mpto` (↦)
- Extensible: `\xto{above}{below}`, `\xincto{}{}`

## Theorem Environments

```latex
\begin{theorem}[Optional Name]
  Statement of the theorem.
\end{theorem}

\begin{proof}
  Proof goes here.
\end{proof}
```

Available environments:
- `theorem`, `lemma`, `proposition`, `corollary`
- `definition`, `example`, `remark`, `note`
- `exercise`, `question`, `warning`
- `axiom`, `assumption`, `convention`

Framed versions: `\begin{framedtheorem}`, `\begin{framedlemma}`, etc.

## TikZ Integration

GWiki includes the `tz.sty` package with many TikZ conveniences:

```latex
% Inline TikZ
\tz{\draw (0,0) -- (1,1);}

% TikZ environment with automatic baseline
\begin{tkz}
  \node (A) {$A$};
  \node (B) at (2,0) {$B$};
  \draw[->] (A) -- (B);
\end{tkz}

% Commutative diagrams (tikz-cd)
\begin{tikzcd}
  A \ar[r, "f"] \ar[d, "g"'] & B \ar[d, "h"] \\
  C \ar[r, "k"'] & D
\end{tikzcd}
```

## HTML Output with LWarp

To generate HTML:

1. Ensure LWarp is installed: `tlmgr install lwarp`
2. Run: `make html`
3. For TikZ diagrams, also run: `lwarpmk limages`

The HTML output uses MathJax for math rendering and generates SVG images for TikZ diagrams.

## Build Commands

| Command | Description |
|---------|-------------|
| `make` | Build all PDFs |
| `make html` | Build all HTML |
| `make all` | Build PDF and HTML |
| `make article ID=x` | Build single article |
| `make wiki ID=x` | Build single wiki note |
| `make new-article ID=x TITLE="..."` | Create new article |
| `make new-wiki ID=x TITLE="..."` | Create new wiki note |
| `make index` | Regenerate index files |
| `make graph` | Generate dependency graph |
| `make watch` | Auto-rebuild on changes |
| `make clean` | Remove build artifacts |
| `make help` | Show all commands |

## Index Files

Running `make index` generates JSON files in `index/`:

- `index.json` - Complete index with all metadata
- `articles.json` - Article metadata
- `wiki.json` - Wiki note metadata
- `backlinks.json` - Backlink references
- `tags.json` - Documents organized by tag
- `graph.json` - Graph data for visualization

## Requirements

- LaTeX distribution (TeX Live recommended)
- Required packages: `thmtools`, `tcolorbox`, `tikz`, `tikz-cd`, `hyperref`, `cleveref`, `newpxtext`, `newpxmath`
- For HTML: LWarp package
- For index generation: Python 3
- For graph visualization: graphviz (optional)

Install required LaTeX packages:
```bash
tlmgr install thmtools tcolorbox tikz-cd hyperref cleveref newpx lwarp
```

## Customization

### Document Class Options

```latex
\documentclass[
  type=article,        % or wiki
  gwikiid=unique-id,
  fontsize=12pt,
  paper=letterpaper,
  margins=1in,
  parskip=false,       % paragraph spacing
  fancyhead=true,      % fancy headers
  index=true,          % generate index
  lwarp=true,          % enable HTML generation
]{gwiki}
```

### Adding Custom Macros

Edit `lib/gwiki-macros.sty` to add your own macros.

### Styling HTML Output

Edit `assets/css/gwiki.css` to customize the HTML appearance.

## Philosophy

GWiki is designed around these principles:

1. **LaTeX-first**: Full LaTeX power without compromise
2. **Interconnected**: Easy linking makes knowledge a graph, not a forest
3. **Automated**: Minimize manual work; let scripts handle bookkeeping
4. **Dual output**: PDF for print/archival, HTML for web accessibility
5. **Separation of concerns**: Content in `.tex`, styling in classes/CSS

## License

MIT License - feel free to use and modify for your own knowledge base.

## Contributing

Contributions welcome! Please open an issue or pull request.
