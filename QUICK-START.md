# 🚀 GWiki Quick Start - No Terminal Required!

## Just Double-Click These Files:

### 📖 **OPEN-WEB-INDEX.command**
**What it does:** Opens the beautiful web index in your browser

**Use this to:**
- Search all your notes instantly
- Browse notes by tag
- See recently created notes
- View statistics (note count, tags, links)

**Demo:**
1. Double-click `OPEN-WEB-INDEX.command`
2. Browser opens with gorgeous purple gradient interface
3. Type in search box to filter notes in real-time
4. Click tabs to switch between All Notes | By Tag | Recent
5. Click any note to read it in HTML with full math rendering

---

### ✏️ **CREATE-NEW-NOTE.command**
**What it does:** Creates a new note with a friendly dialog box

**Use this to:**
- Quickly create new notes without typing commands
- Automatically get proper formatting and dates

**Demo:**
1. Double-click `CREATE-NEW-NOTE.command`
2. Dialog appears: "Enter note title:"
   - Type: `Sobolev space`
3. Next dialog: "Enter tags:"
   - Type: `analysis, PDEs` (or leave empty)
4. Dialog asks: "Open in editor?"
   - Click "Yes" to start editing immediately
5. Your note opens in TextEdit/VS Code/whatever your default editor is

**What happens behind the scenes:**
- File created at `notes/sobolev space.tex`
- Template inserted with title and tags
- Creation date recorded automatically
- File opened in your editor

---

### 🔨 **BUILD-ALL.command**
**What it does:** Builds PDFs and HTML version of all notes

**Use this to:**
- Compile all your LaTeX notes to PDF
- Generate web version with navigation
- Update the master index

**Demo:**
1. Double-click `BUILD-ALL.command`
2. Terminal window shows progress:
   ```
   📄 Building PDFs...
   3-manifold
   functor
   category
   ...
   ✓ 19 PDFs → pdfs/

   🌐 Building web version...
   ✓ 19 HTML files → html/

   📑 Generating indices...
   ✓ Master index → index.html
   ```
3. Press any key when done
4. Browser opens with updated web index

---

## Typical Workflow (All GUI!)

### Morning: Create Notes
1. Double-click **CREATE-NEW-NOTE.command**
2. Enter title: "Banach space"
3. Enter tags: "functional-analysis, topology"
4. Edit the note in your editor
5. Save and close

### Afternoon: Build & Browse
1. Double-click **BUILD-ALL.command**
2. Wait for build to complete
3. Web index opens automatically
4. Search for "Banach" to find your new note
5. Click to read it with beautiful formatting

### Evening: Review & Connect
1. Double-click **OPEN-WEB-INDEX.command**
2. Browse "By Tag" to see all functional-analysis notes
3. Click any note
4. See "Linked Notes" section (notes you reference)
5. See "Backlinks" section (notes that reference this one)

---

## Web Index Features Demo

### Search Box
- **Type:** "category"
- **Instant filter:** Only notes with "category" in title/tags appear
- **Clear search:** Delete text, all notes reappear

### Tabs
- **All Notes:** Alphabetical A-Z grouping
  - Click letter headings to jump
  - See tags next to each note
- **By Tag:** Notes grouped by topic
  - Each tag shows note count: "category-theory (3)"
  - All notes under each tag listed
- **Recent:** Newest notes first
  - Date shown: "2025-12-09"
  - Quick access to what you just created

### Statistics
Three boxes at the top:
- **19** Total Notes
- **15** Tags
- **47** Total Links

### Navigation
- Click any note → Opens in HTML
- At top of each note: "← Back to Index"
- Each note has Table of Contents if 3+ sections
- "Linked Notes" shows where you can go
- "Backlinks" shows how you got here

---

## HTML Note Features Demo

Open any note from the web index to see:

### Navigation Bar (Purple Gradient)
- "← Back to Index" always visible
- Click to return to master index

### Header Section
- **Title** in large blue text
- **Metadata box** (gray background):
  - Last modified: 2025-12-11 17:19
  - Created: 2025-12-09
  - Tags: category-theory, definition

### Table of Contents (Blue Box)
- Appears if note has 3+ sections
- Click section name to jump
- Example: "Definition" → jumps to Definition section

### Content Area
- **Math rendering** via MathJax: $f: X \to Y$
- **TikZ diagrams** via TikZJax: commutative diagrams render!
- **Environments** styled with colors:
  - Yellow: Definition
  - Blue: Theorem/Lemma
  - Purple: Example
  - Cyan: Idea
  - Gray: Remark

### Footer Sections
- **Linked Notes:** Other notes you reference
  - Click to follow the link
- **Backlinks:** Notes that link to this one
  - See your knowledge graph connections

---

## Keyboard Shortcuts (macOS)

### In Web Index
- **⌘+F:** Search (same as clicking search box)
- **⌘+R:** Refresh to see updates
- **⌘+Click note:** Open in new tab

### In HTML Note
- **⌘+F:** Find text in note
- **← Back button:** Return to index
- **⌘+Click link:** Open linked note in new tab

---

## File Organization (You Don't Need to Touch These!)

```
GWiki/
├── 📂 notes/              ← Your LaTeX source files
├── 📂 pdfs/               ← Built PDFs (open with Preview)
├── 📂 html/               ← HTML notes (open in browser)
├── 📄 index.html          ← Master web index (MAIN ENTRY POINT)
│
├── 🚀 OPEN-WEB-INDEX.command      ← Double-click to browse
├── 🚀 CREATE-NEW-NOTE.command     ← Double-click to create
├── 🚀 BUILD-ALL.command           ← Double-click to build
│
└── 📖 QUICK-START.md      ← You are here!
```

---

## Tips & Tricks

### 1. Bookmark the Web Index
Add `file:///Users/greysonwesley/Desktop/GWiki/index.html` to your browser bookmarks for instant access.

### 2. Create Desktop Shortcut
Drag `OPEN-WEB-INDEX.command` to your desktop or Dock for one-click access.

### 3. Set Default Editor
macOS will remember your choice when you click "Open in editor?" in the create dialog.

### 4. Search is Smart
- Searches titles, tags, AND summaries
- Case-insensitive
- Partial matches work ("cat" finds "category")

### 5. Tags are Flexible
- Use hyphens: "category-theory" ✓
- Use spaces: "low dimensional topology" ✓
- Mix and match: "category-theory, PDEs, topology"

---

## Demo Scenario: Complete Workflow

**Goal:** Create a note about Hilbert spaces, link it to existing notes, then view on web.

### Step 1: Create the Note
1. Double-click **CREATE-NEW-NOTE.command**
2. Title: `Hilbert space`
3. Tags: `functional-analysis, topology`
4. Click "Yes" to open in editor

### Step 2: Write Content
```latex
\documentclass{gwiki}
\usepackage{gwiki-links}

\Title{Hilbert space}
\Tags{functional-analysis, topology}

\begin{document}
\NoteHeader

A Hilbert space is a complete inner product space.

\begin{definition}
Let $H$ be a vector space over $\mathbb{C}$. An inner product is...
\end{definition}

See also: \wref{Banach space} (every Hilbert space is a Banach space).

\end{document}
```

### Step 3: Build Everything
1. Save and close editor
2. Double-click **BUILD-ALL.command**
3. Wait 10 seconds
4. Browser opens automatically

### Step 4: Explore Your Work
1. Search box: Type "hilbert"
2. Click "Hilbert space" in results
3. See your formatted note with math rendering
4. Scroll to bottom: "Linked Notes" shows "Banach space"
5. Click "Banach space" to follow the link
6. See "Backlinks" section now includes "Hilbert space"

### Step 5: Browse by Topic
1. Click "← Back to Index"
2. Click "By Tag" tab
3. Find "functional-analysis" section
4. See both "Hilbert space" and "Banach space" listed together

**Total clicks:** 6 (plus typing content)
**Terminal commands:** 0

---

## Troubleshooting

### "Nothing happens when I double-click .command file"
**Fix:** Right-click → Open With → Terminal.app
Then macOS will remember for future double-clicks.

### "No notes appear in web index"
**Fix:** Double-click **BUILD-ALL.command** to generate everything.

### "Math doesn't render in HTML"
**Fix:** Make sure you're online (MathJax loads from CDN).
If offline, math will show as LaTeX code.

### "Links are broken in HTML notes"
**Fix:** Don't move HTML files out of the `html/` folder.
The index expects them there.

---

## Questions?

- Read `FEATURES.md` for complete feature list
- Read `README.md` for command-line options (advanced)
- Open an issue on GitHub for bugs

**Enjoy your beautiful mathematical knowledge base! 📚✨**
