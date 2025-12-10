# GWiki Quick Reference

## Daily Workflow

```bash
# Create note
make new NAME="Stokes theorem" TITLE="Stokes theorem"

# Edit in your editor
vim "notes/Stokes theorem.tex"

# Build everything
make vault
```

## Commands

| Command | Purpose |
|---------|---------|
| `make` | Build all notes to PDFs |
| `make vault` | **Build everything** (validate + bibliography + PDFs + index) |
| `make validate` | Check for broken `\wref` links |
| `make bibliography` | Generate `references.bib` from citations |
| `make index` | Generate vault index |
| `make clean` | Remove all build artifacts |
| `make new NAME="..."` | Create new note |

## Note Template

```latex
\documentclass{gwiki}

\Title{note title here}
\Tags{tag1, tag2}
\Summary{One sentence summary.}
\CreatedOn{YYYY-MM-DD}

\begin{document}

\KeySources{\nlab{page}, \arxiv{1234.5678}}

\NoteHeader

Your content goes here.

\SeeAlso{related-note-1, related-note-2}

\References

\Footer

\end{document}
```

## Linking

```latex
% Link to another note
\wref{functor}

% Link with display text
\wref[display text]{functor}

% Link to section
\wref{functor#sec:composition}

% Related notes
\SeeAlso{category, natural-transformation}
```

## Citations

```latex
% arXiv papers (auto-fetches metadata)
\arxiv{2301.12345}

% nLab pages (auto-generates entry)
\nlab{Grothendieck-universe}

% BibTeX (need to add to references.bib or system will stub)
\cite{Witten1988}
```

## File Naming

- **Use spaces**: `Green function.tex` ✓
- **Not hyphens**: `Green-function.tex` ✗
- **Capitalize proper nouns only**: `Cauchy–Schwarz inequality` ✓
- **Not Title Case**: `Cauchy-Schwarz Inequality` ✗

## Special Commands

```latex
% Key sources (appears in header)
\KeySources{\nlab{page}, \arxiv{1234.5678}}

% Idea box
\begin{framedidea}
The key insight is...
\end{framedidea}

% Related notes
\SeeAlso{note1, note2}

% Reference section
\References
```

## Metadata Files

- `.gwiki-metadata.json` - Creation dates & backlinks (auto-maintained)
- `references.bib` - Bibliography (auto-generated)
- `index.tex` - Vault index (auto-generated)

**Don't edit these manually - they're regenerated automatically.**

## Tips

1. **Always use `make vault`** for a complete build with validation
2. **Creation dates are set once** and never change
3. **Modified dates update automatically** from file timestamps
4. **Broken links show warnings** but don't fail builds
5. **Bibliography auto-updates** - just add citations and rebuild
6. **Spaces in filenames are fine** - the system handles them
7. **Install `pip install -r requirements.txt`** for full bibliography features (optional)

## Troubleshooting

**"Broken link" warning?**
- Create the target note with `make new NAME="target"`
- Or fix the `\wref{target}` reference

**Bibliography not fetching?**
- Install dependencies: `pip install -r requirements.txt`
- System creates stubs if dependencies missing

**Creation date wrong?**
- First creation is tracked automatically
- Don't manually edit `\CreatedOn{}` - it's set once

**Build fails?**
- Check LaTeX syntax errors
- Ensure all `{` `}` are balanced
- Look at actual LaTeX error output (not hidden in `make vault`)
