# GWiki Bibliography System

This directory contains the global bibliography system for GWiki.

## Directory Structure

```
references/
├── references.bib       # Global BibTeX file (all citations)
├── pdfs/               # Local PDF files for references
│   ├── MacLane1978.pdf
│   ├── Lurie2009.pdf
│   └── ...
└── README.md           # This file
```

## Quick Start

### 1. Enable Bibliography in Your Note

Add the `bibliography` option to your document class:

```latex
\documentclass[bibliography]{gwiki}
```

### 2. Add References to `references.bib`

Add your BibTeX entries to `references/references.bib`:

```bibtex
@book{MacLane1978,
  author    = {Mac Lane, Saunders},
  title     = {Categories for the Working Mathematician},
  year      = {1978},
  publisher = {Springer},
}
```

### 3. Add PDF Files

Place PDF files in `references/pdfs/` with filenames matching BibTeX keys:
- BibTeX key: `MacLane1978`
- PDF file: `references/pdfs/MacLane1978.pdf`

### 4. Cite in Your Notes

```latex
\wcite{MacLane1978}              % [Mac78]
\wcite[p. 42]{MacLane1978}       % [Mac78, p. 42]
\wcite[See][Ch. 5]{MacLane1978}  % [See Mac78, Ch. 5]
```

Citations automatically link to local PDFs if they exist!

### 5. Print Bibliography

At the end of your note:

```latex
\References  % Automatically uses BibTeX when bibliography option is enabled
```

## Citation Commands

### Basic Citations

- `\wcite{key}` - Standard citation with PDF link: `[Mac78]`
- `\wcite[p. 42]{key}` - Citation with page: `[Mac78, p. 42]`
- `\wcite[See][Ch. 5]{key}` - With prenote and postnote: `[See Mac78, Ch. 5]`

### Text Citations

- `\wtextcite{key}` - Text citation: `Mac Lane (1978)`
- `\wparencite{key}` - Parenthetical: `(Mac Lane 1978)`
- `\wfullcite{key}` - Full citation inline

### Direct PDF Links

- `\wpdf{key}` - Link to PDF (displays key as text)
- `\wpdf[Click here]{key}` - Link with custom text

### Combined Citation + PDF Link

- `\wcitepdf{key}` - Shows citation with PDF icon link

## Features

### Automatic PDF Linking

When you click a citation in your compiled PDF, it opens the corresponding PDF file from `references/pdfs/` if it exists.

### Hybrid System

- BibTeX entries (in `references.bib`): Full bibliography integration, PDF linking, backref
- Inline citations (not in .bib): Falls back to simple `[Author, Year]` format
- Both types work seamlessly together!

### Backref

The bibliography shows which pages cite each reference.

### Integration with KeySources

You can use BibTeX keys in `\KeySources`:

```latex
\KeySources{\wcite{MacLane1978}, \nlab{category}}
```

## Compilation

When using the bibliography system, you need to run:

```bash
pdflatex yourfile.tex
biber yourfile
pdflatex yourfile.tex
pdflatex yourfile.tex
```

Or use the Makefile which handles this automatically:

```bash
make category  # Compiles notes/category.tex with bibliography
```

## BibTeX Entry Types

Common entry types for mathematics/physics:

- `@article` - Journal articles
- `@book` - Books
- `@incollection` - Book chapters
- `@inproceedings` - Conference papers
- `@phdthesis` - PhD dissertations
- `@misc` - Preprints, notes, etc.
- `@online` - Web resources

## Tips

1. **Consistent Naming**: Use `AuthorYear` format for BibTeX keys (e.g., `MacLane1978`)
2. **PDF Filenames**: Match PDF filenames exactly to BibTeX keys
3. **Organize PDFs**: Keep all PDFs in `references/pdfs/` for easy management
4. **One Global .bib**: Keep all references in one file for consistency
5. **Add Metadata**: Include DOI, URL, arXiv IDs when available

## Example Note

See `notes/category.tex` for an example using the bibliography system.

## Troubleshooting

**Citations show as [?]**
- Run `biber` after `pdflatex`
- Check that BibTeX key is spelled correctly
- Verify entry exists in `references.bib`

**PDF links don't work**
- Check PDF filename matches BibTeX key exactly
- Verify PDF is in `references/pdfs/`
- Try absolute path in `\gwiki@pdfdir` if needed

**Bibliography doesn't appear**
- Use `\References` at end of document
- Make sure at least one citation is used
- Check for LaTeX compilation errors

## Migration from Old System

Old inline citations still work:

```latex
\wcite{Smith2020}  % If Smith2020 not in .bib, displays: [Smith2020]
```

You can gradually migrate by adding entries to `references.bib`.
