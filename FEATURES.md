# GWiki Features & Quality-of-Life Improvements

## New Quality-of-Life Features (December 2025)

### 1. Master Index System

**What it does:** Automatically organizes all your notes in multiple ways

**Features:**
- **Beautiful web index** (`index.html`) with gradient header and search
- **Three LaTeX indices** (alphabetical, by-tag, chronological) in `indices/`
- **Real-time search** filters notes by title, tags, or content
- **Tag grouping** shows all notes under each topic
- **Recent notes** view sorted by creation date
- **Statistics** displays total notes, tags, and links

**Usage:**
```bash
make indices    # Generate all indices
open index.html # View web index
```

**Screenshot of web index:**
- Clean gradient purple header
- Search box for instant filtering
- Three tabs: All Notes | By Tag | Recent
- Note counts and statistics
- Clickable tags on each note

---

### 2. Enhanced HTML Conversion

**What it does:** Converts LaTeX notes to beautiful, navigable HTML pages

**Features:**
- **Top navigation bar** with "Back to Index" link
- **Table of contents** auto-generated for notes with 3+ sections
- **Better styling** with clean typography and colors
- **Metadata box** shows creation/modification dates and tags
- **Backlinks section** shows which notes reference this one
- **Linked notes** displays all outgoing references
- **MathJax support** for all LaTeX math
- **TikZJax support** for diagrams (with full `tz.sty` integration)

**Usage:**
```bash
make html                                    # Convert all notes
python3 scripts/tex-to-html.py notes/X.tex  # Convert single note
```

**Visual improvements:**
- Clean white content area on light background
- Purple gradient navigation bar
- Compact metadata in monospace font
- Blue TOC box with section links
- Hover effects on all links
- Responsive design

---

### 3. Quick Note Creation Script

**What it does:** Creates new notes with proper formatting in seconds

**Features:**
- **Automatic filename** from title (preserves spaces)
- **Template generation** with all necessary commands
- **Date tracking** records creation time immediately
- **Optional editor launch** opens note in `$EDITOR`
- **Helpful feedback** shows next steps

**Usage:**
```bash
./scripts/new-note.sh "Banach space" "functional-analysis, topology"
./scripts/new-note.sh "Green function"  # Tags optional
```

**Template includes:**
- `\documentclass{gwiki}`
- `\Title{}`, `\Tags{}`
- `\NoteHeader`
- Ready-to-edit placeholder

---

### 4. Integrated Build System

**What it does:** One command builds everything you need

**New targets:**
```bash
make web      # Build HTML + master index
make indices  # Generate all index files
make html     # Convert all notes to HTML
make vault    # Now includes indices
```

**Improved output:**
- Clear progress messages
- File counts for each operation
- Color-coded success indicators
- Organized directory structure

**Directory organization:**
```
GWiki/
├── pdfs/      # PDF outputs
├── html/      # HTML outputs
├── indices/   # LaTeX index files
├── build/     # Temporary files
└── index.html # Master web index
```

---

### 5. Tag Organization & Extraction

**What it does:** Automatically finds and groups notes by tags

**Features:**
- **Flexible tag parsing** handles multiple formats:
  - `\Tags{tag1, tag2}` (comma-separated)
  - `\Tags{tag1}{tag2}` (braced)
  - Mixed formats
- **Tag grouping** in indices shows note count per tag
- **Untagged detection** shows notes without tags
- **Tag statistics** in web index

**Usage:** Just use `\Tags{}` in your notes, system handles the rest

---

### 6. Advanced Search & Filtering

**What it does:** Find notes instantly in the web interface

**Features:**
- **Real-time filtering** as you type
- **Multi-field search** matches title, tags, and summaries
- **Case-insensitive** search
- **Instant results** no page reload

**Try it:** Open `index.html` and type in the search box

---

### 7. Improved Link Validation

**Already present, but note the improvements:**
- Compact output format
- 4-digit line numbers with leading zeros
- Suppressed LaTeX noise
- Easy to grep/parse

---

## Usage Patterns

### Daily Workflow
```bash
# 1. Create new note
./scripts/new-note.sh "Sobolev space" "analysis, PDEs"

# 2. Edit note
vim "notes/sobolev space.tex"

# 3. Build
make

# 4. View PDF
open "pdfs/sobolev space.pdf"
```

### Publish to Web
```bash
# Build web version
make web

# Serve locally (requires Python)
python3 -m http.server 8000

# Visit http://localhost:8000
```

### Maintenance
```bash
# Validate all links
make validate

# Regenerate bibliography
make bibliography

# Rebuild everything
make clean && make vault
```

---

## Technical Details

### Master Index Generator
- **File:** `scripts/generate-master-index.py`
- **Reads:** `.gwiki-metadata.json` for dates and links
- **Outputs:**
  - `index.html` (web index)
  - `indices/index-alphabetical.tex`
  - `indices/index-by-tag.tex`
  - `indices/index-chronological.tex`

### HTML Converter
- **File:** `scripts/tex-to-html.py`
- **Features:**
  - Extracts title, tags, summary
  - Converts environments (definition, theorem, idea, etc.)
  - Handles TikZ diagrams
  - Generates TOC from sections
  - Computes backlinks
  - Adds navigation

### Note Creation
- **File:** `scripts/new-note.sh`
- **Features:**
  - Validates title
  - Creates proper filename
  - Generates template
  - Records creation date
  - Opens in editor

---

## File Organization

### Input Files (you create)
```
notes/
├── 3-manifold.tex
├── functor.tex
└── category.tex
```

### Output Files (auto-generated)
```
pdfs/          # PDF notes
html/          # HTML notes
indices/       # LaTeX indices
index.html     # Master web index
.gwiki-metadata.json  # Internal metadata
```

### Supporting Files
```
lib/
├── gwiki.cls         # Document class
├── gwiki-links.sty   # Linking package
└── tz.sty           # TikZ shortcuts

scripts/
├── generate-master-index.py  # NEW
├── tex-to-html.py            # IMPROVED
├── new-note.sh               # NEW
├── track-creation-dates.py
├── validate-links.py
├── generate-bibliography.py
└── generate-backlinks.py
```

---

## Configuration

### Custom Tags
Just use them in `\Tags{}`, the system auto-detects all tags.

### Styling
- **PDF:** Edit `lib/gwiki.cls` and `lib/gwiki-links.sty`
- **HTML:** Edit CSS in `scripts/tex-to-html.py` (lines 980-1153)
- **Web index:** Edit CSS in `scripts/generate-master-index.py`

### Search Editor
Set your preferred editor:
```bash
export EDITOR=vim     # or nano, emacs, code, etc.
./scripts/new-note.sh "note title"
```

---

## Comparison: Before vs After

### Before
```bash
# Create note manually
vim notes/banach-space.tex  # Manual hyphenation
# Write boilerplate...
# Set dates manually
make
# No web version
# No master index
# Hard to find notes
```

### After
```bash
# Create note with script
./scripts/new-note.sh "Banach space" "analysis"
# Opens in editor, dates automatic
make web
# Beautiful web index with search
# HTML version with backlinks & TOC
# Find notes instantly
```

### Before: Finding Notes
- Manually search file system
- Read file headers one by one
- No tag organization

### After: Finding Notes
- Open `index.html`
- Use search box or filter by tag
- See recent notes, statistics
- Click through backlinks

---

## Future Enhancements (Ideas)

- [ ] Graph visualization of note connections
- [ ] Export to Anki flashcards
- [ ] Automatic tag suggestions based on content
- [ ] Note templates (definition-template, theorem-template, etc.)
- [ ] Git integration for note history
- [ ] Mobile-optimized HTML
- [ ] Dark mode for web interface
- [ ] RSS feed for recent notes
- [ ] PDF compilation on file save (watch mode)

---

## Credits

Built with:
- LaTeX (TeX Live)
- Python 3
- GNU Make
- MathJax (web math rendering)
- TikZJax (web diagram rendering)

System design emphasizes:
- **Automation** over manual work
- **Simplicity** over complexity
- **Speed** over features
- **Consistency** over flexibility
