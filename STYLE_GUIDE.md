# GWiki Style Guide & Recommendations

This guide provides stylistic recommendations and best practices for maintaining a high-quality mathematical wiki using GWiki.

## Table of Contents

1. [Writing Philosophy](#writing-philosophy)
2. [Note Structure](#note-structure)
3. [Mathematical Writing Style](#mathematical-writing-style)
4. [Citation Practices](#citation-practices)
5. [Organizational Recommendations](#organizational-recommendations)
6. [Visual Design](#visual-design)
7. [Cross-Referencing Strategy](#cross-referencing-strategy)

---

## Writing Philosophy

### Core Principles

1. **Clarity over Comprehensiveness**: Each note should explain one concept clearly rather than exhaustively covering all aspects.

2. **Interconnection over Isolation**: Use `\wref{}` liberally to create a web of knowledge. Don't repeat definitions—link to them.

3. **Motivation before Definition**: Start with intuition (use `\begin{idea}`), then provide formal definitions.

4. **Examples are Essential**: Every definition deserves at least one concrete example.

### The Idea Box

Always include an idea box at the start of your note:

```latex
\begin{idea}[Core Concept]
What is the essential insight? Why does this concept exist?
What problem does it solve?
\end{idea}
```

**Good example:**
```latex
\begin{idea}
A sheaf captures the idea of locally-defined data that can be
consistently glued together—like how local coordinates on a
manifold patch together to give global structure.
\end{idea}
```

**Bad example:**
```latex
\begin{idea}
Sheaves are important in algebraic geometry and topology.
\end{idea}
```

---

## Note Structure

### Recommended Template

```latex
\documentclass[bibliography]{gwiki}

\Title{Your Concept}
\Tags{main-field, subfield, type}
\Summary{One sentence capturing the essence of this concept.}

\begin{document}

\NoteHeader

\begin{idea}[Core Insight]
The essential intuition in 2-3 sentences.
\end{idea}

\KeySources{\wcite{MainReference}, \nlab{concept}}

\section{Definition}

\begin{definition}[Formal Name]
Precise mathematical definition.
\end{definition}

\section{Examples}

\begin{example}
Concrete, accessible example.
\end{example}

\begin{example}
More sophisticated example.
\end{example}

\section{Properties}

\begin{proposition}
Key properties with proofs or references.
\end{proposition}

\section{Related Concepts}

\SeeAlso{related-note-1, related-note-2}

\References

\Footer

\end{document}
```

### Section Organization

**For Definition Notes** (category, functor, sheaf):
1. Idea
2. Definition
3. Examples
4. Properties
5. Related Concepts

**For Theorem Notes** (Stokes' theorem, Yoneda lemma):
1. Idea/Motivation
2. Statement
3. Sketch of Proof (or full proof)
4. Applications
5. Related Results

**For Theory Notes** (Donaldson theory, K-theory):
1. Idea/Overview
2. Historical Context
3. Main Definitions
4. Key Results
5. Applications
6. Further Directions

---

## Mathematical Writing Style

### Theorem Environments

Use framed environments for important results:

```latex
\begin{framedtheorem}[Stokes' Theorem]
Let $\omega$ be a differential $(n-1)$-form on an oriented
$n$-manifold $M$ with boundary $\partial M$. Then
\[
\int_M d\omega = \int_{\partial M} \omega
\]
\end{framedtheorem}
```

Use plain environments for routine statements:

```latex
\begin{proposition}
The composition of functors is associative.
\end{proposition}
```

### Naming Conventions

**Definitions**: Use bold for the term being defined
```latex
A \textbf{category} $\cC$ consists of...
```

**First mention**: Italicize or use standard font
```latex
Every category has an \emph{opposite category} $\cC^{op}$.
```

**Subsequent mentions**: Standard font
```latex
The opposite category reverses all morphisms.
```

### Proof Style

**Short proofs**: Inline with paragraph structure
```latex
\begin{proof}
This follows immediately from associativity of composition.
\end{proof}
```

**Medium proofs**: Use structured paragraphs
```latex
\begin{proof}
We verify the axioms individually.

\paragraph{Associativity} ...

\paragraph{Identity} ...
\end{proof}
```

**Long proofs**: Use steps or claims
```latex
\begin{proof}
\begin{step}[Construct the map]
Define $f: X \to Y$ by...
\end{step}

\begin{step}[Verify continuity]
Let $U$ be open in $Y$...
\end{step}
\end{proof}
```

### Display Math

**Simple equations**: Inline when they fit naturally
```latex
The equation $E = mc^2$ is Einstein's famous relation.
```

**Important formulas**: Display even if short
```latex
The Euler characteristic satisfies:
\[
\chi(X) = V - E + F
\]
```

**Long derivations**: Use `align` or `gather`
```latex
\begin{align}
  \int_M d\omega &= \int_M d(fdx) \\
                 &= \int_M f'(x)dx \\
                 &= f(b) - f(a)
\end{align}
```

### Lists

**Enumerate with `lst`**: For numbered items with math
```latex
\begin{lst}
  \item Objects $\Obj(\cC)$
  \item Morphisms $\Hom(A,B)$
  \item Composition $\circ$
\end{lst}
```

**Itemize**: For unnumbered lists
```latex
\begin{itemize}
  \item First point
  \item Second point
\end{itemize}
```

---

## Citation Practices

### When to Use Bibliography vs. Inline References

**Use BibTeX** (`\wcite`) for:
- Books and textbooks
- Journal articles
- PhD theses
- Foundational papers
- Sources you reference frequently across multiple notes

**Use inline references** for:
- Quick mentions without formal citation
- General attribution
- Temporary placeholders

**Use `\arxiv` and `\nlab`** for:
- Preprints and online notes
- nLab articles (community wiki content)

### KeySources Best Practices

List 1-3 primary references that most directly inform your note:

```latex
\KeySources{\wcite{MacLane1978}, \nlab{category}}
```

**Good KeySources:**
- The original paper introducing the concept
- The standard textbook treatment
- The most accessible exposition

**Not for KeySources:**
- Every reference mentioned in the note
- Historical curiosities
- Tangentially related works

### Citation Style in Text

**First mention of major result:**
```latex
Donaldson's theorem \wcite{Donaldson1983} established that...
```

**Referring to a specific part:**
```latex
For a comprehensive treatment, see \wcite[Ch. 2]{Freed1995}.
```

**Multiple citations:**
```latex
This perspective appears in several sources
\wcite{MacLane1978, Lurie2009}.
```

### PDF Management

**Naming convention:**
- BibTeX key: `AuthorYear` or `AuthorYearShortTitle`
- PDF filename: exactly matches key

**Folder structure:**
```
references/
├── references.bib
└── pdfs/
    ├── MacLane1978.pdf
    ├── Lurie2009.pdf
    └── AtiyahSinger1968.pdf
```

**Finding PDFs:**
1. Author's webpage (often has preprints)
2. arXiv (if available)
3. Journal (institutional access)
4. Legal repositories (SpringerLink, JSTOR via institution)

---

## Organizational Recommendations

### Tagging Strategy

**Use 2-4 tags per note:**

```latex
\Tags{category-theory, definition}           % Minimal
\Tags{algebraic-topology, cohomology, duality}  % Field + concept + property
```

**Tag hierarchy:**
1. **Field**: `category-theory`, `differential-geometry`, `algebraic-topology`
2. **Type**: `definition`, `theorem`, `construction`, `example`
3. **Topic**: `functors`, `manifolds`, `homology`
4. **Property**: `duality`, `classification`, `invariant`

**Consistent tag names:**
- Use lowercase, hyphenated: `gauge-theory` not `Gauge Theory`
- Plural for general topics: `categories`, `sheaves`
- Singular for specific concepts: `functor`, `sheaf`

### Aliases

Use aliases for common alternate names:

```latex
\Aliases{categories, CT}                    % Category
\Aliases{QFT, quantum field theories}        % Quantum Field Theory
\Aliases{ASD connections, instantons}        % Anti-Self-Dual Connections
```

### Note Naming

**File names**: lowercase, hyphenated, descriptive
- `category.tex` ✓
- `yoneda-lemma.tex` ✓
- `lie-group.tex` ✓
- `Category.tex` ✗ (avoid caps)
- `yl.tex` ✗ (not descriptive)

**Titles**: Proper mathematical capitalization
```latex
\Title{Category}                  % Concept
\Title{Yoneda Lemma}             % Named theorem
\Title{Lie Group}                % Mathematical object
\Title{Stokes' Theorem}          % Proper name + theorem
```

### Directory Organization

Keep notes flat in `notes/`, use tags for organization:

```
notes/
├── category.tex
├── functor.tex
├── natural-transformation.tex
├── yoneda-lemma.tex
└── ...
```

**Don't create subdirectories** like `notes/category-theory/`. The index and tags handle organization.

---

## Visual Design

### Color-Coded Environments

GWiki color-codes enunciations for visual scanning:

- **Blue**: Theorems, Propositions (statements to prove)
- **Yellow/Gold**: Lemmas (helper results)
- **Green**: Examples
- **Olive**: Definitions, Facts
- **Purple**: Propositions
- **Cyan**: Ideas
- **Gray**: Remarks, Notes

Use framed environments strategically:

```latex
\begin{framedtheorem}[Main Result]  % Important, stands out
...
\end{framedtheorem}

\begin{proposition}                  % Routine, subtle
...
\end{proposition}
```

### TikZ Diagrams

**Use `tz.sty` for commutative diagrams:**

```latex
\begin{center}
\begin{tikzcd}
  X \arrow[r, "f"] \arrow[d, "g"'] & Y \arrow[d, "h"] \\
  Z \arrow[r, "k"'] & W
\end{tikzcd}
\end{center}
```

**Label important diagrams:**

```latex
\begin{equation}\label{diag:pullback}
\begin{tikzcd}
  ...
\end{tikzcd}
\end{equation}
```

### Typography

**Fonts:**
- Serif (default) for body text
- Sans-serif (`\sffamily`) for headers (automatic)
- Typewriter (`\texttt`) for code, URLs

**Emphasis:**
- `\textbf{bold}` for definitions
- `\emph{italic}` for emphasis
- `\textsl{slanted}` for links (automatic)

**Spacing:**
- Use `\medskip` / `\bigskip` for vertical space
- Don't manually add `\\` for spacing
- Let LaTeX handle paragraph spacing

---

## Cross-Referencing Strategy

### Internal References (within note)

```latex
\section{Definitions}\label{sec:definitions}

\begin{definition}[Category]\label{def:category}
...
\end{definition}

Later: See \cref{def:category} in \cref{sec:definitions}.
```

### External References (between notes)

**Simple link:**
```latex
See \wref{functor} for details.
```

**Custom text:**
```latex
Every \wref[natural transformation]{natural-transformation} is...
```

**Link to specific section:**
```latex
See the proof in \wref{yoneda-lemma#sec:proof}.
```

**Reference specific result:**
```latex
By \wintref[Yoneda]{yoneda-lemma}{thm:main}, we have...
```

### Building a Web of Knowledge

**Strategy:**
1. **Define once, link everywhere**: Don't restate definitions
2. **Bidirectional links**: If note A references B, consider if B should reference A
3. **Context chains**: Create paths like: `category → functor → natural-transformation → yoneda-lemma`
4. **Hub notes**: Make foundational concepts (like `category`) central hubs

**Link density:**
- First mention of a concept: always link
- Subsequent mentions: link if jumping to that note would be helpful
- Don't over-link common terms (like "group" in an algebra note)

### See Also Sections

```latex
\SeeAlso{related-concept-1, related-concept-2, advanced-topic}
```

**Guidelines:**
- List 2-5 related notes
- Order by relevance/dependency
- Include both prerequisites and extensions

---

## Advanced Recommendations

### Maintaining Consistency

**Create a personal glossary note:**
```latex
% glossary.tex - your notation conventions
$\cC$ for categories
$\Set$ for the category of sets
$\Hom(A,B)$ for morphism sets
```

**Reference it in notes that might vary:**
```latex
We use the notation from \wref{glossary}.
```

### Progressive Enhancement

**Start simple:**
1. Write basic definition + idea + one example
2. Compile and verify
3. Add more examples
4. Add properties/theorems
5. Improve cross-references
6. Add citations from .bib

**Don't let perfect be the enemy of good**: A note with just an idea box and definition is better than no note.

### Version Control Practices

**Commit messages:**
```bash
git commit -m "Add Donaldson theory note with bibliography"
git commit -m "Update category note: add slice category example"
git commit -m "Fix typo in Yoneda lemma proof"
```

**Branch for major reorganizations:**
```bash
git checkout -b reorganize-topology-notes
# Make changes
git merge reorganize-topology-notes
```

### Regular Maintenance

**Monthly tasks:**
- Run `make vault` to rebuild index
- Review tags for consistency
- Update bibliography with new sources
- Fix broken cross-references

**Quarterly tasks:**
- Review older notes for quality
- Add missing examples to sparse notes
- Consolidate duplicate information
- Update citations with published versions of preprints

---

## Examples of Well-Structured Notes

### Minimal Definition Note

```latex
\documentclass{gwiki}

\Title{Pushout}
\Tags{category-theory, limits}
\Summary{The categorical generalization of glueing.}

\begin{document}
\NoteHeader

\begin{idea}
A pushout glues two objects along a common subobject—like
gluing two topological spaces along a common subspace.
\end{idea}

\begin{definition}[Pushout]
Given morphisms $f: A \to B$ and $g: A \to C$ in a category $\cC$,
a \textbf{pushout} is an object $P$ with morphisms $i: B \to P$ and
$j: C \to P$ satisfying $i \circ f = j \circ g$ that is universal
among such objects.
\end{definition}

\SeeAlso{pullback, colimit, category}

\Footer
\end{document}
```

### Rich Theorem Note

```latex
\documentclass[bibliography]{gwiki}

\Title{Yoneda Lemma}
\Tags{category-theory, theorem, fundamental}
\Summary{Natural transformations from a representable functor correspond to elements.}

\begin{document}
\NoteHeader

\begin{idea}
An object is completely determined by its relationships to all other objects—
like how a space is determined by all possible maps into it.
\end{idea}

\KeySources{\wcite{MacLane1978}, \nlab{yoneda-lemma}}

\section{Statement}

\begin{framedtheorem}[Yoneda Lemma]\label{thm:yoneda}
For any \wref{functor} $F: \cC \to \Set$ and object $A \in \cC$,
\[
\mathrm{Nat}(\Hom(A,-), F) \cong F(A)
\]
naturally in both $A$ and $F$.
\end{framedtheorem}

\section{Proof Sketch}
... detailed proof ...

\section{Corollaries}

\begin{corollary}[Yoneda Embedding]
The \wref{functor} $\cC \to [\cC^{op}, \Set]$ given by $A \mapsto \Hom(-,A)$
is fully faithful.
\end{corollary}

\SeeAlso{representable-functor, natural-transformation}

\References
\Footer
\end{document}
```

---

## Summary: Quick Checklist

Before finalizing a note:

- [ ] Idea box present and insightful
- [ ] Summary is one clear sentence
- [ ] 2-4 relevant tags
- [ ] At least one concrete example
- [ ] Cross-references to related notes
- [ ] Bibliography enabled if using citations
- [ ] PDFs placed in `references/pdfs/`
- [ ] Compiles without errors
- [ ] KeySources lists primary references (if applicable)

---

**Remember**: GWiki is your personal knowledge base. These are guidelines, not rigid rules. Adapt them to your workflow and mathematical interests.
