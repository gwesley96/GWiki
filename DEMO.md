# 🎬 GWiki Live Demo - Visual Walkthrough

## What You See When You Use Each Feature

---

## 🖱️ Demo 1: Open Web Index

### Action
**Double-click:** `OPEN-WEB-INDEX.command`

### What Happens
1. **Terminal window appears** (2 seconds):
   ```
   ✓ Opened web index in browser
     You can now search and browse all your notes!
   ```

2. **Browser opens** showing:

   ```
   ┌─────────────────────────────────────────────────────┐
   │                      GWiki                          │
   │           A mathematical knowledge base             │
   └─────────────────────────────────────────────────────┘
   ┌─────────────┬─────────────┬─────────────┐
   │   19        │     15      │     47      │
   │ Total Notes │    Tags     │ Total Links │
   └─────────────┴─────────────┴─────────────┘

   ┌─────────────────────────────────────────────────────┐
   │ Search notes by title, tags, or content...         │
   └─────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────┐
   │  All Notes  │  By Tag  │  Recent                   │
   └─────────────────────────────────────────────────────┘

   A
   ─────────────────────────────────────────────────────
   abelian category [category-theory, definition]

   B
   ─────────────────────────────────────────────────────
   Birkhoff Duality [order-theory, lattice-theory]

   C
   ─────────────────────────────────────────────────────
   category [category-theory, definition]
   cochain complex
   Cohomology [higher-category-theory, homotopy-theory]
   ```

3. **Try typing in search box:**
   - Type: `cat`
   - **Instant filter:** Only shows "category", "abelian category"
   - Type: `theory`
   - **Shows all:** category-theory tagged notes

4. **Click "By Tag" tab:**
   ```
   category-theory (3)
   ─────────────────────────────────────────────────────
   category
   functor
   natural transformation

   functional-analysis (2)
   ─────────────────────────────────────────────────────
   Gelfand transform

   differential-geometry (3)
   ─────────────────────────────────────────────────────
   parallel transport via a connection
   (pseudo-)Riemannian metric
   ```

5. **Click "Recent" tab:**
   ```
   Recently Created
   ─────────────────────────────────────────────────────
   2025-12-09  3-manifold [low-dimensional-topology]
   2025-12-09  functor [category-theory, definition]
   2025-12-09  category [category-theory, definition]
   ```

---

## 🖱️ Demo 2: Create New Note

### Action
**Double-click:** `CREATE-NEW-NOTE.command`

### What Happens

#### Step 1: Title Dialog
```
┌──────────────────────────────────────────┐
│         Create New Note                  │
├──────────────────────────────────────────┤
│  Enter note title:                       │
│  ┌────────────────────────────────────┐  │
│  │ Sobolev space                      │  │
│  └────────────────────────────────────┘  │
│                                          │
│              [ Cancel ]  [ OK ]          │
└──────────────────────────────────────────┘
```
**You type:** `Sobolev space`
**Click:** OK

#### Step 2: Tags Dialog
```
┌──────────────────────────────────────────┐
│         Create New Note                  │
├──────────────────────────────────────────┤
│  Enter tags (comma-separated, or leave   │
│  empty):                                 │
│  ┌────────────────────────────────────┐  │
│  │ analysis, PDEs                     │  │
│  └────────────────────────────────────┘  │
│                                          │
│              [ Cancel ]  [ OK ]          │
└──────────────────────────────────────────┘
```
**You type:** `analysis, PDEs`
**Click:** OK

#### Step 3: Terminal Shows Progress
```
✓ Created: notes/sobolev space.tex

Next steps:
  1. Edit notes/sobolev space.tex
  2. make         # Build PDF
  3. make web     # Build HTML version
```

#### Step 4: Open in Editor Dialog
```
┌──────────────────────────────────────────┐
│         Create New Note                  │
├──────────────────────────────────────────┤
│  Note created: notes/sobolev space.tex   │
│                                          │
│  Open in editor?                         │
│                                          │
│               [ No ]  [ Yes ]            │
└──────────────────────────────────────────┘
```
**Click:** Yes

#### Step 5: TextEdit/VS Code Opens
```latex
\documentclass{gwiki}
\usepackage{gwiki-links}

\Title{Sobolev space}
\Tags{analysis, PDEs}

\begin{document}
\NoteHeader

%% Write your note here...
█ (cursor here - ready to type!)


\end{document}
```

**Now you can:**
- Start typing your content
- Save when done (⌘+S)
- Close editor

---

## 🖱️ Demo 3: Build Everything

### Action
**Double-click:** `BUILD-ALL.command`

### What Happens

#### Terminal Window Shows:
```
════════════════════════════════════════
  GWiki: Building Everything
════════════════════════════════════════

📄 Building PDFs...
3-manifold
functor
category
cochain complex
Cohomology
dg algebra
abelian category
Birkhoff Duality
Gelfand transform
looping and delooping
natural transformation
parallel transport via a connection
Donaldson theory
Drinfeld twist of a Hopf algebra
Haag Duality
Hstar monad
tikz demo
(pseudo-)Riemannian metric
(n+epsilon)D TQFT
sobolev space                    ← Your new note!

✓ 20 PDFs → pdfs/

🌐 Building web version...
  ✓ 20 HTML files → html/

📑 Generating indices...
  ✓ Master index → index.html
  ✓ LaTeX indices → indices/

════════════════════════════════════════
  ✅ BUILD COMPLETE!
════════════════════════════════════════

Output:
  • PDFs:  pdfs/
  • HTML:  html/
  • Index: index.html

Press any key to open web index...
```

**You press:** Space bar (or any key)

**Browser opens** with updated index showing your new note!

---

## 🖱️ Demo 4: Browse Your New Note

After building, the web index opens. Now:

### Step 1: Search for Your Note
In search box, type: `sobolev`

**Results filter instantly:**
```
S
─────────────────────────────────────────────────────
Sobolev space [analysis, PDEs]
```

### Step 2: Click the Note
Browser navigates to: `html/sobolev space.html`

**You see:**
```
┌─────────────────────────────────────────────────────┐
│ ← Back to Index                                     │
└─────────────────────────────────────────────────────┘
╔═══════════════════════════════════════════════════╗
║                 Sobolev space                      ║
╚═══════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────┐
│ Last modified: 2025-12-11 17:45                     │
│ Created: 2025-12-11                                 │
│ Tags: analysis, PDEs                                │
└─────────────────────────────────────────────────────┘

[Your content here with beautiful formatting]

─────────────────────────────────────────────────────
Linked Notes
─────────────────────────────────────────────────────
(If you added \wref{other note}, it appears here)

─────────────────────────────────────────────────────
Backlinks
─────────────────────────────────────────────────────
(Notes that link to this one appear here)
```

### Step 3: Navigate Back
**Click:** `← Back to Index` at top

**Returns to:** Main index

---

## 🖱️ Demo 5: Explore By Tags

### In Web Index, Click "By Tag" Tab

**You see all your tags with counts:**
```
analysis (1)
─────────────────────────────────────────────────────
Sobolev space

category-theory (3)
─────────────────────────────────────────────────────
category
functor
natural transformation

differential-geometry (3)
─────────────────────────────────────────────────────
parallel transport via a connection
(pseudo-)Riemannian metric

functional-analysis (2)
─────────────────────────────────────────────────────
Gelfand transform

higher-category-theory (1)
─────────────────────────────────────────────────────
Cohomology

PDEs (1)
─────────────────────────────────────────────────────
Sobolev space
```

**Notice:** Your new note appears under both "analysis" AND "PDEs"!

---

## 🖱️ Demo 6: View HTML Note with Math & Diagrams

### Click Any Math-Heavy Note (e.g., "functor")

**Browser shows beautifully rendered:**

```
┌─────────────────────────────────────────────────────┐
│ ← Back to Index                                     │
└─────────────────────────────────────────────────────┘
╔═══════════════════════════════════════════════════╗
║                    functor                         ║
╚═══════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────┐
│ Last modified: 2025-12-11 17:19                     │
│ Created: 2025-12-09                                 │
│ Tags: category-theory, definition                   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Contents                                            │
│ • Definition                                        │
│ • Examples                                          │
│ • Properties                                        │
└─────────────────────────────────────────────────────┘

Definition
─────────────────────────────────────────────────────
A functor F : C → D between categories consists of...

[Math renders beautifully:]
  F(f ∘ g) = F(f) ∘ F(g)
  F(id_X) = id_{F(X)}

Examples
─────────────────────────────────────────────────────
[If there's a TikZ diagram, it renders as SVG!]

─────────────────────────────────────────────────────
Linked Notes
─────────────────────────────────────────────────────
category
natural transformation

─────────────────────────────────────────────────────
Backlinks
─────────────────────────────────────────────────────
natural transformation
Cohomology
```

**Notice:**
- Math is rendered (not LaTeX code)
- Table of contents appears (3+ sections)
- Links are clickable
- Backlinks show connections

---

## 🎯 Complete Workflow Example

### Scenario: You want to write notes on functional analysis

#### Monday Morning
1. **Double-click:** `CREATE-NEW-NOTE.command`
2. **Create:** "Banach space" with tags "functional-analysis"
3. **Write content** in editor, save

4. **Double-click:** `CREATE-NEW-NOTE.command` again
5. **Create:** "Hilbert space" with tags "functional-analysis"
6. **Write content**, reference Banach: `\wref{Banach space}`
7. **Save**

#### Monday Afternoon
1. **Double-click:** `BUILD-ALL.command`
2. **Wait** 10 seconds for build
3. **Browser opens** automatically

#### Browse Your Work
1. **Click:** "By Tag" tab
2. **Find:** "functional-analysis (2)"
3. **See:** Both notes listed together
4. **Click:** "Hilbert space"
5. **Scroll down:** See "Banach space" under "Linked Notes"
6. **Click:** "Banach space" to follow link
7. **Scroll down:** See "Hilbert space" under "Backlinks"!

**You just:**
- Created 2 interconnected notes
- Built PDFs and web version
- Browsed your knowledge graph
- Never typed a terminal command!

---

## 📱 macOS Integration Tips

### Dock Shortcuts
Drag these to your Dock for one-click access:
- `OPEN-WEB-INDEX.command` → Daily browsing
- `CREATE-NEW-NOTE.command` → Quick note creation

### Desktop Shortcuts
Drag to Desktop:
- `BUILD-ALL.command` → After editing session

### Finder Sidebar
Add GWiki folder to Finder sidebar:
1. Open Finder
2. Drag `GWiki` folder to sidebar under "Favorites"
3. Quick access to all `.command` files

### Spotlight Search
Press ⌘+Space, type:
- "create new note" → Finds `CREATE-NEW-NOTE.command`
- "gwiki" → Finds all GWiki files

---

## 🎨 Visual Summary

### Files You Double-Click
```
GWiki/
├── 🟣 OPEN-WEB-INDEX.command      ← Browse notes
├── 🟢 CREATE-NEW-NOTE.command     ← Make new note
└── 🔵 BUILD-ALL.command           ← Compile everything
```

### What You Get
```
Browser:
  index.html → Beautiful searchable index
    ↓ click note
  html/note.html → Formatted note with math
    ↓ click link
  html/other.html → Connected notes
```

### The Magic
- **No terminal commands**
- **No LaTeX knowledge needed** (templates provided)
- **No file path typing** (dialogs handle it)
- **No manual linking** (backlinks automatic)
- **No search implementation** (built-in real-time)

---

## 🚀 You're Ready!

**Just remember these three files:**

1. **OPEN-WEB-INDEX.command** = Browse
2. **CREATE-NEW-NOTE.command** = Write
3. **BUILD-ALL.command** = Publish

Everything else is automatic! 🎉
