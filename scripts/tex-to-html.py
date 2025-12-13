#!/usr/bin/env python3
"""
GWiki LaTeX to HTML Converter
Converts GWiki LaTeX notes to standalone HTML pages with MathJax and TikZJax
"""

import re
import sys
import os
from pathlib import Path
from datetime import datetime

def extract_metadata(content):
    """Extract title and tags from LaTeX source"""
    # Simple regex for Tags is usually ok as they don't contain nested braces often,
    # but Title often contains math or macros.
    
    title = "Untitled"
    if '\\Title{' in content:
        start = content.find('\\Title{') + 7
        # Count braces
        balance = 1
        i = start
        while i < len(content) and balance > 0:
            if content[i] == '{': balance += 1
            elif content[i] == '}': balance -= 1
            i += 1
        
        if balance == 0:
            title = content[start:i-1]

    # Tags still use regex for simplicity as brace counting everything is slow/complex 
    # and Tags usually simple.
    tags_match = re.search(r'\\Tags\{([^}]*)\}', content)
    tags_raw = tags_match.group(1) if tags_match else ""
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()]

    return title, tags

def extract_custom_macros(content):
    """Parse \\newcommand and \\renewcommand definitions from content."""
    macros = {}
    
    # Simple regex for single-line simple macros: \newcommand{\foo}{bar}
    # But we need to handle arguments and nested braces ideally.
    # regex pattern: \(re)?newcommand\s*\{\\(\w+)\}(?:\[(\d+)\])?\{(.*)\}
    # This is hard with regex due to nesting. Let's iterate.
    
    # Matches: \newcommand or \renewcommand
    # Then {\name}
    # Then optional [nargs]
    # Then {body}
    
    idx = 0
    n = len(content)
    while True:
        # Find command start
        match = re.search(r'\\(?:re)?newcommand\s*\{\\(\w+)\}', content[idx:])
        if not match:
            break
            
        name = match.group(1)
        rel_start = match.end()
        cur = idx + rel_start
        
        # Check for optional args [n]
        nargs = 0
        while cur < n and content[cur].isspace(): cur += 1
        
        if cur < n and content[cur] == '[':
            # Parse [n] - usually just a digit
            end_opt = content.find(']', cur)
            if end_opt != -1:
                try:
                    nargs = int(content[cur+1:end_opt])
                except:
                    pass
                cur = end_opt + 1
        
        # Parse body { ... }
        while cur < n and content[cur].isspace(): cur += 1
        
        if cur < n and content[cur] == '{':
            # Use brace balancer
            start_body = cur
            balance = 1
            cur += 1
            while cur < n and balance > 0:
                if content[cur] == '{': balance += 1
                elif content[cur] == '}': balance -= 1
                cur += 1
            
            if balance == 0:
                body = content[start_body+1 : cur-1]
                # Store
                if nargs > 0:
                     macros[name] = [body, nargs] # Store as list for MathJax
                else:
                     macros[name] = body
        
        idx = cur
        
    return macros

def extract_body(content):
    r"""Extract content between \NoteHeader and \References"""
    # 1. Try extracting between \NoteHeader and \References or \Footer
    match = re.search(r'\\NoteHeader\s*(.*?)(?=\\References\b|\\Footer\b)', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 2. Try extracting from \NoteHeader to \end{document}
    match = re.search(r'\\NoteHeader\s*(.*)', content, re.DOTALL)
    if match:
        body = match.group(1)
        # Find the LAST \end{document} to valid nesting
        last_end = body.rfind(r'\end{document}')
        if last_end != -1:
            return body[:last_end].strip()
        return body.strip()

    # 3. Fallback: \begin{document} to \end{document}
    match = re.search(r'\\begin\{document\}(.*)', content, re.DOTALL)
    if match:
        body = match.group(1)
        # Try to strip \NoteHeader if it exists but wasn't caught above (e.g. whitespace issues)
        body = re.sub(r'\\NoteHeader', '', body, count=1)
        
        last_end = body.rfind(r'\end{document}')
        if last_end != -1:
            return body[:last_end].strip()
        return body.strip()

    return ""


def build_title_map(notes_dir):
    """Scan all .tex files to build a filename -> title map"""
    title_map = {}
    if not os.path.exists(notes_dir):
        return title_map
        
    for f in os.listdir(notes_dir):
        if f.endswith('.tex'):
            path = os.path.join(notes_dir, f)
            try:
                content = Path(path).read_text(encoding='utf-8')
                match = re.search(r'\\Title\{([^}]+)\}', content)
                if match:
                    title = match.group(1)
                    # Use filename (without ext) as key
                    name = os.path.splitext(f)[0]
                    title_map[name] = title
            except:
                pass
    return title_map

def convert_wikilinks(text, title_map=None):
    """Convert \wref links to HTML links with title lookup."""
    def repl(match):
        display = match.group('display') or match.group('display_after')
        target = match.group('target')
        
        # If no display text is provided, try to look up the title
        if not display:
            if title_map and target in title_map:
                display = title_map[target]
            else:
                # Fallback: prettify filename (e.g. "banach-algebra" -> "Banach Algebra")
                # Don't force title case, just replace hyphens with spaces
                display = target.replace('-', ' ')
                
        return f'<a href="{target}.html">{display}</a>'

    pattern = re.compile(
        r'\\wref(?:\[(?P<display>[^\]]+)\])?\{(?P<target>[^}]+)\}(?:\[(?P<display_after>[^\]]+)\])?'
    )
    return pattern.sub(repl, text)

def convert_bold(text):
    """Convert **bold** to <strong>bold</strong>"""
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text

def convert_latex_bold(text):
    """Convert \\textbf{...} to <strong>...</strong>"""
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', text)
    return text

def convert_italic(text):
    """Convert *italic* to <em>italic</em>"""
    return re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

def convert_emph(text):
    """Convert \\emph{...} to <em>...</em>"""
    return re.sub(r'\\emph\{(.*?)\}', r'<em>\1</em>', text)

def convert_textit(text):
    """Convert \\textit{...} to <em>...</em>"""
    return re.sub(r'\\textit\{(.*?)\}', r'<em>\1</em>', text)

def convert_quotes(text):
    """Convert ``...'' to “...” and `...' to ‘...’"""
    text = re.sub(r"``", "“", text)
    text = re.sub(r"''", "”", text)
    text = re.sub(r"`", "‘", text)
    text = re.sub(r"'", "’", text)
    return text

def convert_texttt(text):
    """Convert \\texttt{...} to <code>...</code>"""
    # Use loop to handle nested braces or multiple occurrences robustly
    # But for texttt simple regex usually suffices if no nested braces
    # Let's use robust regex that handles one level of nesting if possible, or non-greedy
    return re.sub(r'\\texttt\{([^}]+)\}', r'<code>\1</code>', text)

def convert_specialchars(text):
    """Convert LaTeX special characters like \\textbackslash"""
    text = text.replace(r'\textbackslash', '\\')
    return text

def convert_texorpdfstring(text, prefer_text=False):
    """Convert \\texorpdfstring{TeX}{PDF} -> TeX or PDF"""
    # Regex to capture two balanced groups
    # This is tricky with regex, simpler with loop if nested.
    # Assuming standard non-nested usage for now or use the consume_group helper if available/replicated.
    
    # Simple regex for non-nested braces
    # text = re.sub(r'\\texorpdfstring\{([^}]*)\}\{([^}]*)\}', r'\1', text) 
    
    # Robust loop approach
    out = []
    i = 0
    n = len(text)
    while i < n:
        match = text.find(r'\texorpdfstring', i)
        if match == -1:
            out.append(text[i:])
            break
            
        out.append(text[i:match])
        
        # Move past command
        cur = match + 15 # len('\texorpdfstring')
        
        # Skip space?
        while cur < n and text[cur].isspace(): cur += 1
            
        # Parse 1st arg (TEX)
        if cur < n and text[cur] == '{':
            tex_content, cur = parse_balanced(text, cur)
        else:
            # Error or malformed
            out.append(text[match:match+15]) # restore command
            i = match + 15
            continue
            
        # Parse 2nd arg (PDF)
        while cur < n and text[cur].isspace(): cur += 1
        if cur < n and text[cur] == '{':
            pdf_content, cur = parse_balanced(text, cur)
        else:
             # Malformed
             out.append(text[match:match+15])
             i = match + 15
             continue
             
        if prefer_text:
            out.append(pdf_content)
        else:
            out.append(tex_content)
        
        i = cur
        
    result = "".join(out)
    return result

def strip_comments(text):
    """Strip LaTeX comments, handling escaped percent signs."""
    # This is complex because of lines.
    # We should iterate line by line or use a robust pattern.
    # Pattern: % followed by anything until newline, but NOT if preceded by \
    return re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)


def parse_balanced(text, start_idx):
    """Helper to parse literal balanced braces returning content inside."""
    if start_idx >= len(text) or text[start_idx] != '{':
        return "", start_idx
    
    balance = 1
    i = start_idx + 1
    content_start = i
    while i < len(text) and balance > 0:
        if text[i] == '{': balance += 1
        elif text[i] == '}': balance -= 1
        i += 1
        
    return text[content_start:i-1], i

def convert_markdown_links(text):
    """Convert [text](url) to <a href="url">text</a>"""
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

def convert_href(text):
    """Convert \\href{url}{text} to <a href="url">text</a>"""
    # Simple regex for balanced braces (assuming non-nested for URLs)
    def repl(match):
        url = match.group(1).replace(r'\%', '%')
        label = match.group(2)
        return f'<a href="{url}">{label}</a>'
        
    pattern = r'\\href\{([^}]+)\}\{(.*?)\}'
    return re.sub(pattern, repl, text)

def convert_labels(text):
    """Convert \\label{foo} to <a id="foo"></a>, sanitizing the ID."""
    def repl(match):
        label = match.group(1)
        safe_id = re.sub(r'[^a-zA-Z0-9\-_]', '-', label)
        return f'<a id="{safe_id}" class="latex-label"></a>'
        
    return re.sub(r'\\label\{([^}]+)\}', repl, text)

def replace_command_robust(text, cmd_name, repl_template):
    """
    Robustly replace \\cmd{arg} with repl_template.format(arg).
    Handles nested braces in arg.
    """
    out_text = []
    idx = 0
    n = len(text)
    cmd_len = len(cmd_name)
    
    while idx < n:
        # Find next command
        match = text.find(cmd_name, idx)
        if match == -1:
            out_text.append(text[idx:])
            break
            
        out_text.append(text[idx:match])
        
        # Check if valid command (not suffix of another)
        # and followed by brace or space then brace
        cur = match + cmd_len
        
        while cur < n and text[cur].isspace():
            cur += 1
            
        if cur < n and text[cur] == '{':
            content, end_pos = parse_balanced(text, cur)
            replacement = repl_template.format(content)
            out_text.append(replacement)
            idx = end_pos
        else:
            # Not a match (e.g. \defnz or \defn without brace)
            out_text.append(text[match:match+cmd_len]) # Append command itself
            idx = match + cmd_len
            
    return "".join(out_text)



def convert_refs(text):
    """Convert \\ref, \\cref, \\eqref to HTML links"""
    def sanitize(label):
         return re.sub(r'[^a-zA-Z0-9\-_]', '-', label)

    # \cref{label}
    def repl_cref(match):
        label = match.group(1)
        safe_id = sanitize(label)
        # simplistic display: just the label or "Reference"
        # Ideally we'd know the counter, but we don't.
        # Use the label ID itself as text for now.
        return f'<a href="#{safe_id}" class="latex-ref">{label}</a>'

    # \ref{label}
    def repl_ref(match):
        label = match.group(1)
        safe_id = sanitize(label)
        return f'<a href="#{safe_id}" class="latex-ref">{label}</a>'

    # \eqref{label} -> (ref)
    def repl_eqref(match):
        label = match.group(1)
        safe_id = sanitize(label)
        return f'(<a href="#{safe_id}" class="latex-ref">{label}</a>)'

    text = re.sub(r'\\cref\{([^}]+)\}', repl_cref, text)
    text = re.sub(r'\\ref\{([^}]+)\}', repl_ref, text)
    text = re.sub(r'\\eqref\{([^}]+)\}', repl_eqref, text)
    return text

def convert_tikz(text):
    """Convert tikz code blocks, inline tikzcd, tkz environment, and \tz command to TikZJax."""
    
    # helper to stash content to protect from regexes
    verb_blocks = []
    def stash_verb(match):
        verb_blocks.append(match.group(0))
        return f'__VERB_BLOCK_{len(verb_blocks) - 1}__'
    
    # Stash \verb|...|

    # Stash \verb|...|
    text = re.sub(r'\\verb(?P<delim>[^a-zA-Z]).*?(?P=delim)', stash_verb, text, flags=re.DOTALL)
    # Stash \begin{verbatim}...\end{verbatim}
    text = re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', stash_verb, text, flags=re.DOTALL)
    # Stash \begin{lstlisting}...\end{lstlisting}
    text = re.sub(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', stash_verb, text, flags=re.DOTALL)

    tikz_blocks = []
    def stash_script(script_content):
        tikz_blocks.append(script_content)
        return f'__TIKZ_BLOCK_{len(tikz_blocks) - 1}__'

    # Helper to wrap content in script tag with preamble
    def wrap_tikz(content, preamble=True):
        full_content = (TIKZ_PREAMBLE + "\n" + content) if preamble else content
        return f'<script type="text/tikz">{full_content}</script>'

    # 1. Handle ```tikz ... ``` blocks
    def repl_block(match):
        content = match.group(1)
        return stash_script(wrap_tikz(content))
    
    text = re.sub(r'```tikz\s*(.*?)\s*```', repl_block, text, flags=re.DOTALL)

    # 2. Handle \begin{tkz}[opt] ... \end{tkz}
    def repl_tkz(match):
        opt = match.group(1) if match.group(1) else ""
        content = match.group(2)
        # Reconstruct the full tikzpicture code
        if opt:
            tikz_code = f'\\begin{{tikzpicture}}[{opt}]\n{content}\n\\end{{tikzpicture}}'
        else:
            tikz_code = f'\\begin{{tikzpicture}}\n{content}\n\\end{{tikzpicture}}'
        return stash_script(wrap_tikz(tikz_code))

    text = re.sub(r'\\begin\{tkz\}(?:\[([^\]]*)\])?(.*?)\\end\{tkz\}', repl_tkz, text, flags=re.DOTALL)

    text = re.sub(r'\\begin\{tkz\}(?:\[([^\]]*)\])?(.*?)\\end\{tkz\}', repl_tkz, text, flags=re.DOTALL)

    # 3. Handle \tz[opt]{content} - Manual scan for nested braces
    out_text = []
    idx = 0
    n = len(text)
    while idx < n:
        # Find next \tz
        next_tz = text.find(r'\tz', idx)
        if next_tz == -1:
            out_text.append(text[idx:])
            break
            
        # Append text before \tz
        out_text.append(text[idx:next_tz])
        
        # Check if valid command start
        # \tz followed by [ or { or space?
        cursor = next_tz + 3 # len(\tz)
        
        # Save start pos to revert if no match
        match_start = next_tz
        
        # Skip spaces
        while cursor < n and text[cursor].isspace():
            cursor += 1
            
        # Optional arg
        opt = ""
        has_opt = False
        if cursor < n and text[cursor] == '[':
            # Consume balanced [...]
            opt_start = cursor + 1
            balance = 1
            cursor += 1
            while cursor < n and balance > 0:
                if text[cursor] == '[': balance += 1
                elif text[cursor] == ']': balance -= 1
                cursor += 1
            if balance == 0:
                opt = text[opt_start:cursor-1]
                has_opt = True
            else:
                # Open bracket but no close? Abort
                out_text.append(text[match_start:cursor])
                idx = cursor
                continue

        # Skip spaces
        while cursor < n and text[cursor].isspace():
            cursor += 1

        # Mandatory arg usually starts with {
        if cursor < n and text[cursor] == '{':
            # Consume balanced {...}
            body_start = cursor + 1
            balance = 1
            cursor += 1
            while cursor < n and balance > 0:
                if text[cursor] == '{': balance += 1
                elif text[cursor] == '}': balance -= 1
                cursor += 1
                
            if balance == 0:
                body = text[body_start:cursor-1]
                # Found it!
                tikz_code = f'\\begin{{tikzpicture}}[{opt}]\n{body}\n\\end{{tikzpicture}}'
                replacement = stash_script(wrap_tikz(tikz_code))
                out_text.append(replacement)
                idx = cursor
                continue
            else:
                # Unbalanced
                out_text.append(text[match_start:cursor])
                idx = cursor
                continue
                
        # If we get here, it wasn't a valid \tz call (e.g. \tzsomething)
        # But wait, \tz could be just \tz without args? Uncommon for this macro.
        # Check if character after \tz is non-alpha?
        # But we already skipped spaces.
        # If it's `\tz ` (space) or `\tz{`, we proceed.
        # Only if we failed to match { after optional args.
        
        # Just append what we skipped and continue
        out_text.append(text[match_start:cursor])
        idx = cursor
        
    text = "".join(out_text)

    # 4. Handle \begin{tikzcd} ... \end{tikzcd}
    # Matches optional \[ wrapper, then the environment
    def repl_tikzcd(match):
        content = match.group(1)
        # Verify content starts with \begin{tikzcd} to be safe, though regex ensures it
        return stash_script(wrap_tikz(content))

    text = re.sub(r'(?:\\\[\s*)?(\\begin\{tikzcd\}.*?\\end\{tikzcd\})(?:\s*\\\])?', repl_tikzcd, text, flags=re.DOTALL)

    # 5. Handle \begin{tikzpicture}[opt] ... \end{tikzpicture}
    def repl_tikzpicture(match):
        opt = match.group(1) if match.group(1) else ""
        content = match.group(2)
        # Reconstruct the full tikzpicture code
        if opt:
            tikz_code = f'\\begin{{tikzpicture}}[{opt}]\n{content}\n\\end{{tikzpicture}}'
        else:
            tikz_code = f'\\begin{{tikzpicture}}\n{content}\n\\end{{tikzpicture}}'
        return stash_script(wrap_tikz(tikz_code, preamble=False))

    text = re.sub(r'\\begin\{tikzpicture\}(?:\[([^\]]*)\])?(.*?)\\end\{tikzpicture\}', repl_tikzpicture, text, flags=re.DOTALL)
    
    # Restore TikZ blocks
    for i, block in enumerate(tikz_blocks):
        text = text.replace(f'__TIKZ_BLOCK_{i}__', block)
    # Restore verb blocks
    for i, block in enumerate(verb_blocks):
        text = text.replace(f'__VERB_BLOCK_{i}__', block)

    return text

def convert_environments(text):
    """Convert LaTeX environments to HTML divs"""
    # Pattern to match \begin{envname}[optional] ... \end{envname}
    def replace_env(match):
        env_name = match.group(1)
        optional = match.group(2) if match.group(2) else ""
        body = match.group(3).strip()

        # Labels are handled globally now

        # Normalize env name for display
        disp_name = env_name
        if disp_name.startswith('framed'):
            disp_name = disp_name[6:]
            
        # Strip outer braces from optional arg if present (e.g. [{(Cite)}])
        if optional and optional.startswith('{') and optional.endswith('}'):
             optional = optional[1:-1]

        # Special case for Idea: if optional is "Idea", don't repeat it.
        if disp_name == "idea" and optional == "Idea":
             title = f"<strong>{disp_name.capitalize()}.</strong>"
        elif disp_name == "idea":
             # Display as "Idea"
             if optional:
                title = f"<strong>{disp_name.capitalize()} ({optional}).</strong>"
             else:
                title = f"<strong>{disp_name.capitalize()}.</strong>"
        elif optional:
            title = f"<strong>{disp_name.capitalize()} ({optional}).</strong>"
        else:
            title = f"<strong>{disp_name.capitalize()}.</strong>"

        # Content placement logic
        # If body starts with a list (<ul> or <ol>), title goes on separate line/paragraph
        # Use lstrip to ignore potential whitespace/newlines from conversion
        if body.lstrip().startswith('<ul>') or body.lstrip().startswith('<ol>'):
             content = f'<p>{title}</p>\n{body}'
        else:
             # Inline title - we rely on wrap_paragraphs to keep this together if it's text
             content = f'{title} {body}'

        return f'<div class="env-box {env_name}">\n{content}\n</div>'

    # Match environments, including framed versions
    # Added: construction, claim, step, question, warning, exercise, fact, observation,
    # convention, note, notation, axiom, assumption, algorithm, postulate
    env_list = (
        r"definition|theorem|lemma|proposition|corollary|example|remark|idea|"
        r"construction|claim|step|question|warning|exercise|fact|observation|"
        r"convention|note|notation|axiom|assumption|algorithm|postulate"
    )
    # create regex that allows "framed" prefix optionally
    # We use a non-capturing group for the prefix `(?:framed)?` but we need to capture the base name.
    # Actually my previous regex was `(framed)?(definition|...)`.
    # Let's construct it dynamically or just write it out.
    # The previous regex usage relied on group 1 being full name or prefix?
    # Original: `(definition|...|frameddefinition|...)` matches the whole string.
    # I'll just build a big pattern.
    
    # Pre-process restatable: \begin{restatable}{env}{name} ... \end{restatable} -> \begin{env} ... \end{env}
    # We ignore the name for now as the inner env usually handles labeling content or we just don't need it.
    # Note: Regex needs to match balanced braces ideally, but for simple env names {theorem} it's fine.
    text = re.sub(
        r'\\begin\{restatable\}\{([^}]+)\}\{([^}]+)\}(.*?)\\end\{restatable\}',
        r'\\begin{\1}\3\\end{\1}',
        text,
        flags=re.DOTALL
    )

    # Pre-process pf -> proof
    text = re.sub(r'\\begin\{pf\}', r'\\begin{proof}', text)
    text = re.sub(r'\\end\{pf\}', r'\\end{proof}', text)

    envs = [
        "definition", "theorem", "lemma", "proposition", "corollary", "example", "remark", "idea",
        "construction", "claim", "step", "question", "warning", "exercise", "fact", "observation",
        "convention", "note", "notation", "axiom", "assumption", "algorithm", "postulate", "proof",
        "theoremalpha"
    ]
    formatted_envs = "|".join([f"(?:framed)?{e}" for e in envs])
    
    text = re.sub(
        r'\\begin\{(' + formatted_envs + r')\}(?:\[([^\]]+)\])?(.*?)\\end\{\1\}',
        replace_env,
        text,
        flags=re.DOTALL
    )

    return text

# Legacy patterns for TikZJax compatibility (PGF 3.0 vs 3.1)
LEGACY_PATTERNS = r'''
\pgfdeclarepatternformonly{primeddots}{\pgfqpoint{-1pt}{-1pt}}{\pgfqpoint{5pt}{5pt}}{\pgfqpoint{4pt}{4pt}}%
{
  \pgfpathcircle{\pgfqpoint{0pt}{0pt}}{.5pt}
  \pgfusepath{fill}
}
\pgfdeclarepatternformonly{primeddots2}{\pgfqpoint{-.3pt}{-.3pt}}{\pgfqpoint{.3pt}{.3pt}}{\pgfqpoint{2.5pt}{2.5pt}}%
{
  \pgfpathcircle{\pgfqpoint{0pt}{0pt}}{.35pt}
  \pgfusepath{fill}
}
\pgfdeclarepatternformonly{primedbox}{\pgfqpoint{-1pt}{-1pt}}{\pgfqpoint{1pt}{1pt}}{\pgfqpoint{5pt}{5pt}}%
{
  \pgfpathrectangle{\pgfqpoint{-.9pt}{-.9pt}}{\pgfqpoint{1.8pt}{1.8pt}}
  \pgfusepath{stroke}
}
\pgfdeclarepatternformonly{primedplus}{\pgfqpoint{-1pt}{-1pt}}{\pgfqpoint{1pt}{1pt}}{\pgfqpoint{5pt}{5pt}}%
{
  \pgftransformrotate{30}
  \pgfpathmoveto{\pgfqpoint{-.9pt}{-.9pt}}
  \pgfpathlineto{\pgfqpoint{.9pt}{.9pt}}
  \pgfpathmoveto{\pgfqpoint{.9pt}{-.9pt}}
  \pgfpathlineto{\pgfqpoint{-.9pt}{.9pt}}
  \pgfusepath{stroke}
}
\pgfdeclarepatternformonly{primedstar}{\pgfqpoint{-1.2pt}{-1.2pt}}{\pgfqpoint{1.2pt}{1.2pt}}{\pgfqpoint{5pt}{5pt}}%
{
  \pgftransformrotate{30}
  \pgfpathmoveto{\pgfqpoint{-1.2pt}{0pt}}
  \pgfpathlineto{\pgfqpoint{1.2pt}{0pt}}
  \pgfpathmoveto{\pgfqpoint{-.6pt}{-1.04pt}}
  \pgfpathlineto{\pgfqpoint{.6pt}{1.04pt}}
  \pgfpathmoveto{\pgfqpoint{-.6pt}{1.04pt}}
  \pgfpathlineto{\pgfqpoint{.6pt}{-1.04pt}}
  \pgfusepath{stroke}
}
\pgfdeclarepatternformonly{diaglines}{\pgfqpoint{-1pt}{-1pt}}{\pgfqpoint{1pt}{1pt}}{\pgfqpoint{4pt}{4pt}}%
{
  \pgfpathmoveto{\pgfqpoint{-1pt}{-1pt}}
  \pgfpathlineto{\pgfqpoint{1pt}{1pt}}
  \pgfusepath{stroke}
}
\pgfdeclarepatternformonly{hlines}{\pgfqpoint{-1pt}{-.5pt}}{\pgfqpoint{1pt}{.5pt}}{\pgfqpoint{4pt}{3pt}}%
{
  \pgfpathmoveto{\pgfqpoint{-1pt}{0pt}}
  \pgfpathlineto{\pgfqpoint{1pt}{0pt}}
  \pgfusepath{stroke}
}
'''

# Legacy commands replacing xparse \NewDocumentCommand
LEGACY_COMMANDS = r'''
% Simplified \drawmark[color]{coord}[label][pos]
\newcommand{\drawmark}[2][black]{\fill[#1] (#2) circle (\mkrad);}
\newcommand{\drawobject}[2][black]{\draw[thick, fill=#1] (#2) circle (\obrad);}
\newcommand{\mk}[1]{\drawmark{#1}}
\newcommand{\ob}[1]{\drawobject[black]{#1}}
\newcommand{\wob}[1]{\drawobject[white]{#1}}
\newcommand{\umark}[1]{\draw (#1) circle (\mkrad);}
\newcommand{\labmark}[3]{\drawmark{#1}[#2]{#3}}
\newcommand{\labob}[3]{\drawobject[black]{#1}[#2]{#3}}
\newcommand{\blt}[2][]{\node[circle, fill, inner sep=0pt, minimum size=0.1cm, #1] at #2 {};}
\newcommand{\cpn}[3][]{\node[draw, thick, fill=white, rounded corners=3pt, #1] at #2 {#3};}
'''

SAFE_ON_LAYER = r'''
\tikzset{
  on layer/.code={}
}
'''

def strip_command(text, cmd):
    """Strip a command and its balanced arguments from latex text."""
    # Find command
    while True:
        idx = text.find(cmd)
        if idx == -1:
            break
            
        # Check if it is the command (not suffix)
        # simplistic check: followed by { or [ or space
        # But we assume inputs like \tikzdeclarepattern{...}
        
        # Find start of arguments (first { or [)
        # We assume standard latex: \cmd{arg} or \cmd[opt]{arg}
        # For our targets, they are \NewDocumentCommand... or \tikzdeclarepattern...
        
        # We just want to effectively remove the whole block.
        # Simple brace counting from the first {.
        
        pre = text[:idx]
        post = text[idx+len(cmd):]
        
        # Scan forward in post to find first {
        open_idx = post.find('{')
        if open_idx == -1:
             # Weird, just remove command?
             text = pre + post
             continue
             
        # Just remove whitespace between cmd and first {
        # Actually NewDocumentCommand has args like {name}, so it's fine.
        
        # Balance braces starting from open_idx
        balance = 1
        pos = open_idx + 1
        while pos < len(post) and balance > 0:
            if post[pos] == '{':
                balance += 1
            elif post[pos] == '}':
                balance -= 1
            pos += 1
            
        if balance == 0:
            # Found end
            # Also check if there are subsequent arguments?
            # For \NewDocumentCommand{\tz}{...}{...}, there are 3 brace groups!
            # For \tikzdeclarepattern{...}, there is 1.
            
            # Simple heuristic: consume trailing spaces and look for another { immediately?
            # For this specific task, we know:
            # \tikzdeclarepattern{...} -> 1 group
            # \NewDocumentCommand{name}{args}{body} -> 3 groups
            # \NewDocumentEnvironment{name}{args}{begin}{end} -> 4 groups
            
            # Let's just remove the first group for pattern, and assume we handle others by name.
            
            # To be robust, let's hardcode for the known commands.
            pass
            
        # REWRITE: simpler loop
        # We need to handle multiple distinct commands.
        # Let's just regex matching the command name, then consume N mandatory args?
        # Too complex.
        
        # Fallback: Just replace the specific known strings from tz.sty?
        # No, that's brittle.
        
        # Recursive brace stripper implementation:
        
        def consume_brace_group(s):
            start = s.find('{')
            if start == -1: return 0, False
            balance = 1
            i = start + 1
            while i < len(s) and balance > 0:
                if s[i] == '{': balance += 1
                elif s[i] == '}': balance -= 1
                i += 1
            return i, (balance == 0)
            
        # Logic for removal
        current_post = post
        groups_to_remove = 1
        if 'NewDocumentCommand' in cmd: groups_to_remove = 3
        if 'NewDocumentEnvironment' in cmd: groups_to_remove = 4
        if 'tikzdeclarepattern' in cmd: groups_to_remove = 1
        
        total_consumed = 0
        success = True
        
        for _ in range(groups_to_remove):
             length, ok = consume_brace_group(current_post)
             if not ok:
                 success = False
                 break
             total_consumed += length
             current_post = current_post[length:]
             
        if success:
            text = pre + current_post
        else:
             # Failed to match, abort stripping this instance
             if 'NewDocumentCommand' in cmd:
                 # Backup plan: regex replace the command itself and hopefully braces balance out later or don't matter?
                 # No, that's dangerous.
                 # Let's just try to be more robust.
                 # If we can't strip it, maybe we just replace the command name with empty?
                 # text = pre + post # NO - leaves args
                 break
             break
             
    return text

def consume_group(s, open_char='{', close_char='}'):
    start = s.find(open_char)
    if start == -1: return 0, False
    balance = 1
    i = start + 1
    while i < len(s) and balance > 0:
        if s[i] == open_char: balance += 1
        elif s[i] == close_char: balance -= 1
        i += 1
    return i, (balance == 0)

def remove_newcommand(text, cmd_name):
    """Remove a specific \\newcommand definition from text."""
    escaped_cmd = re.escape(cmd_name)
    
    while True:
        # Find \\newcommand followed by {cmd_name} or cmd_name
        match = re.search(r'\\newcommand\s*(?:\{' + escaped_cmd + r'\}|' + escaped_cmd + r'(?![a-zA-Z]))', text)
        if not match:
            break
            
        start_idx = match.start()
        end_idx = match.end()
        
        current_pos = end_idx
        # Consume whitespace
        while current_pos < len(text) and text[current_pos].isspace():
            current_pos += 1
            
        # Optional args (up to 2) - usually [n] and [default]
        for _ in range(2):
            if current_pos < len(text) and text[current_pos] == '[':
                 length, ok = consume_group(text[current_pos:], '[', ']')
                 if ok: 
                     current_pos += length
                 else:
                     break
            # Consume whitespace
            while current_pos < len(text) and text[current_pos].isspace():
                current_pos += 1

        # Mandatory arg (body)
        if current_pos < len(text) and text[current_pos] == '{':
             length, ok = consume_group(text[current_pos:], '{', '}')
             if ok: current_pos += length
             
        # Remove the whole block
        text = text[:start_idx] + text[current_pos:]
        
    return text

def load_tz_sty():
    """Load and clean lib/tz.sty for injection into TikZJax"""
    try:
        root_dir = Path(__file__).resolve().parent.parent
        tz_path = root_dir / "lib" / "tz.sty"
        if not tz_path.exists():
            return ""
        
        with open(tz_path, 'r') as f:
            content = f.read()
            
        # Clean content
        content = re.sub(r'\\NeedsTeXFormat.*', '', content)
        content = re.sub(r'\\ProvidesPackage.*', '', content)
        content = re.sub(r'\\RequirePackage.*', '', content)
        
        # Strip using brace matching
        content = strip_command(content, r'\NewDocumentCommand')
        content = strip_command(content, r'\NewDocumentEnvironment')
        content = strip_command(content, r'\tikzdeclarepattern')
        
        # Remove leftover specific xparse stuff
        content = re.sub(r'\\IfValueT', '', content) # Crude but likely sufficient if args are just braces
        
        
        # Libraries
        content = re.sub(r'\\usetikzlibrary\{.*?\}', '', content, flags=re.DOTALL)
        # content = re.sub(r'\\pgfdeclarelayer\{.*?\}', '', content)
        # content = re.sub(r'\\pgfsetlayers\{.*?\}', '', content)
        
        SAFE_LIBRARIES = r'\usetikzlibrary{arrows.meta,calc,decorations.markings,shapes.geometric,patterns}'

        # Custom cleaning for specific tz.sty constructs
        
        # 1. Remove \tz and \tkz definitions - we handle these in Python
        #    They are likely \NewDocumentCommand{\tz}...
        #    Our strip_command logic should handle them if they use \NewDocumentCommand
        
        # 2. Remove unsafe layer configuration if present (pgfdeclarelayer etc)
        # Use simple recursive braced stripper for these too just to be safe?
        # Or just robust regex
        content = re.sub(r'\\pgfdeclarelayer\s*\{.*?\}', '', content)
        content = re.sub(r'\\pgfsetlayers\s*\{.*?\}', '', content)
        
        # 3. Strip makeatletter blocks (handles on layer, pgfaddtoshape, etc)
        # This removes unsafe internals
        content = re.sub(r'\\makeatletter.*?\\makeatother', '', content, flags=re.DOTALL)
        
        # 4. Strip commands that we replace with legacy versions to prevent "Command already defined" errors
        # List: \mk, \ob, \wob, \umark, \labmark, \labob, \cpn, \blt
        content = remove_newcommand(content, r'\mk')
        content = remove_newcommand(content, r'\ob')
        content = remove_newcommand(content, r'\wob')
        content = remove_newcommand(content, r'\umark')
        content = remove_newcommand(content, r'\labmark')
        content = remove_newcommand(content, r'\labob')
        content = remove_newcommand(content, r'\cpn')
        content = remove_newcommand(content, r'\blt')
        
        # Also clean empty lines left behind
        content = re.sub(r'\n\s*\n', '\n', content)

        # 6. Remove \endinput
        content = re.sub(r'\\endinput', '', content)


        # 5. Explicitly remove on layer style definition if it wasn't stripped so we can override it
        #    It's usually: \tikzset{ on layer/.code={...} }
        #    But it might be complex. SAFE_ON_LAYER will be appended after, so it should override.

        return content + "\n" + SAFE_LIBRARIES + "\n" + SAFE_ON_LAYER + "\n" + LEGACY_PATTERNS + "\n" + LEGACY_COMMANDS
        
    except Exception as e:
        print(f"Warning: Could not load tz.sty: {e}")
        return ""

# TikZJax safe libraries
# Note: matrix, fit, positioning often work but heavy shapes/decorations might fail.
# shapes.misc, shapes.symbols, shapes.multipart are often problematic.
SAFE_LIBRARIES = r'\usetikzlibrary{arrows.meta,calc,decorations.markings,shapes.geometric,patterns,positioning,fit}'

TIKZ_PREAMBLE = r'''
''' + load_tz_sty() + r'''

\newcommand{\wref}[2][]{#2}
'''

def convert_lst(text):
    """Convert LaTeX lst environment to HTML lists"""

    def replace_lst(match):
        optional = match.group(1) if match.group(1) else ""
        content = match.group(2)
        # Split by \item
        items = re.split(r'\s*\\item\s+', content)
        # Filter empty items
        items = [item.strip() for item in items if item.strip()]
        
        # Determine list type based on label/content
        # If label is present (e.g. H*1), maybe we should preserve it?
        # But simpler to just make a list.
        # If optional has label, maybe we could surface it, but <ul> is safe.
        list_html = "<ul>\n"
        
        # If there's a custom label, regular <ul> won't show it.
        # This function generates standard bullets.
        # For now, this fixes the "artifacts" issue.
        
        for item in items:
            list_html += f"<li>{item}</li>\n"
        list_html += "</ul>"
        return list_html

    text = re.sub(r'\\begin\{lst\}(?:\[(.*?)\])?(.*?)\\end\{lst\}', replace_lst, text, flags=re.DOTALL)
    
    # Also handle standard itemize/enumerate
    def replace_itemize(match):
        optional = match.group(1) if match.group(1) else ""
        content = match.group(2)
        items = re.split(r'\s*\\item\s+', content)
        items = [item.strip() for item in items if item.strip()]
        
        # Check for nosep
        css_class = ""
        if "nosep" in optional:
            css_class = ' class="nosep"'
            
        list_html = f"\n<ul{css_class}>\n"
        for item in items:
            list_html += f"<li>{item}</li>\n"
        list_html += "</ul>\n"
        return list_html
        
    text = re.sub(r'\\begin\{itemize\}(?:\[(.*?)\])?(.*?)\\end\{itemize\}', replace_itemize, text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{enumerate\}(?:\[(.*?)\])?(.*?)\\end\{enumerate\}', replace_itemize, text, flags=re.DOTALL)

    return text

def convert_itemize(text):
    """Convert list items to proper HTML lists"""
    lines = text.split('\n')
    result = []
    in_list = False

    list_type = None  # 'ul' for unordered, 'ol' for ordered
    current_item_lines = []
    base_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for list item patterns
        # Match "- " or "- (label) " where label is (i), (ii), (1), (2), etc.
        unordered_match = re.match(r'^(\s*)-\s+(?!\([ivxIVX0-9]+\)\s)(.*)$', line)
        ordered_match = re.match(r'^(\s*)-\s+\(([ivxIVX0-9]+)\)\s+(.*)$', line)

        if unordered_match and not ordered_match:
            # Unordered list item
            indent = unordered_match.group(1)
            item_content = unordered_match.group(2).strip()

            if not in_list or list_type != 'ul':
                if in_list:
                    # Close previous list item
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                result.append('<ul>')
                in_list = True
                list_type = 'ul'
                base_indent = len(indent)
            else:
                # Save previous item
                if current_item_lines:
                    result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                    current_item_lines = []

            current_item_lines.append(item_content)

        elif ordered_match:
            # Ordered list item with label
            indent = ordered_match.group(1)
            label = ordered_match.group(2)
            item_content = ordered_match.group(3).strip()

            if not in_list or list_type != 'ol':
                if in_list:
                    # Close previous list item
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                result.append('<ol>')
                in_list = True
                list_type = 'ol'
                base_indent = len(indent)
            else:
                # Save previous item
                if current_item_lines:
                    result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                    current_item_lines = []

            current_item_lines.append(item_content)

        else:
            # Not a list item start
            if in_list and line.strip():
                # Check if this line is indented and continues the previous item
                # OR if it's display math (starts with \[ or is just \])
                line_indent = len(line) - len(line.lstrip())
                is_display_math = stripped.startswith('\\[') or stripped == '\\]'
                if line_indent > base_indent or is_display_math:
                    # Continuation of current item
                    current_item_lines.append(line.strip())
                else:
                    # End of list
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                    result.append(line)
            elif in_list and not line.strip():
                # Empty line in list - could be end or spacing
                # Look ahead to see if more list items follow
                next_is_list = False
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.match(r'^\s*-\s+', next_line):
                        next_is_list = True

                if not next_is_list:
                    # End list
                    if current_item_lines:
                        result.append('<li>' + ' '.join(current_item_lines) + '</li>')
                        current_item_lines = []
                    result.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                result.append(line)
            else:
                result.append(line)

        i += 1

    # Close any open list at end
    if in_list:
        if current_item_lines:
            result.append('<li>' + ' '.join(current_item_lines) + '</li>')
        result.append(f'</{list_type}>')

    return '\n'.join(result)

def convert_sections(text):
    """Convert markdown-style headers and LaTeX sections to HTML with robust brace handling"""
    # Parse LaTeX sections manually to handle nested braces
    headers = {
        'section': 'h2',
        'subsection': 'h3',
        'subsubsection': 'h4'
    }
    
    out = []
    i = 0
    n = len(text)
    
    while i < n:
        # searching for \section, \subsection, etc.
        # Find next backslash
        match_idx = text.find('\\', i)
        if match_idx == -1:
            out.append(text[i:])
            break
            
        out.append(text[i:match_idx])
        i = match_idx
        
        # Check what command it is
        cmd = None
        cmd_len = 0
        
        # Check for longest match first
        for c in ['subsubsection', 'subsection', 'section']:
            if text.startswith('\\' + c, i):
                # Check if followed by * or {
                after = i + 1 + len(c)
                if after < n:
                    if text[after] == '*':
                        cmd = c
                        cmd_len = 1 + len(c) + 1 # \section*
                    elif text[after] == '{':
                        cmd = c
                        cmd_len = 1 + len(c)
                    # Else it's just the word section
                break
        
        if not cmd:
            out.append(text[i])
            i += 1
            continue
            
        # It's a section command. Parse title.
        cur = i + cmd_len
        while cur < n and text[cur].isspace(): cur += 1
        
        if cur < n and text[cur] == '{':
            title_content, cur = parse_balanced(text, cur)
            
            # Generate ID
            # Strip comments from title processing if any?
            # Clean title for ID: strip latex commands and non-alnum
            clean_title = re.sub(r'<[^>]+>', '', title_content) 
            clean_title = re.sub(r'\\[a-zA-Z]+', '', clean_title) 
            clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', clean_title)
            header_id = clean_title.strip().lower().replace(' ', '-')
            
            # Fallback ID
            if not header_id or header_id == '-':
                header_id = f"section-{cur}"
                
            tag = headers[cmd]
            out.append(f'<{tag} id="{header_id}">{title_content}</{tag}>')
            i = cur
        else:
            # Not a proper section block (e.g. \section without brace?)
            out.append(text[i:1+len(cmd)]) # just append command
            i += 1 + len(cmd)
            continue
            
    # Markdown headers (Keep regex for simple markdown)
    text = "".join(out)
    text = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    return text

def fix_math_colons(text):
    """Replace : with \colon in math expressions like f : A -> B"""
    def replace_colon(match):
        content = match.group(1)
        # Look for : followed by something then an arrow
        # We search for : followed by non-punct chars until an arrow
        # Use simple heuristic: if we see : ... \to without intermediate : or = or ;
        # Capturing group 1 is the content between : and arrow
        content = re.sub(r':([^:=;]*?)(?=\\(?:to|rightarrow|longrightarrow|longmapsto|hookrightarrow|twoheadrightarrow)\b)', r'\\colon\1', content)
        return f'${content}$'

    # Match inline math. Display math is harder (\[...\])
    text = re.sub(r'\$([^$]+)\$', replace_colon, text)
    
    # Simple display math (\[...\])
    def replace_colon_display(match):
        content = match.group(1)
        content = re.sub(r':([^:=;]*?)(?=\\(?:to|rightarrow|longrightarrow|longmapsto|hookrightarrow|twoheadrightarrow)\b)', r'\\colon\1', content)
        return f'\\[{content}\\]'
        
    text = re.sub(r'\\\[(.*?)\\\]', replace_colon_display, text, flags=re.DOTALL)
    
    return text

def convert_seealso(text):
    """Convert \\SeeAlso command. Run BEFORE link converters."""
    def split_balanced(s):
        parts = []
        current = []
        balance_paren = 0
        balance_brack = 0
        balance_brace = 0
        
        for char in s:
            if char == ',' and balance_paren == 0 and balance_brack == 0 and balance_brace == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(char)
                if char == '(': balance_paren += 1
                elif char == ')': balance_paren = max(0, balance_paren - 1)
                elif char == '[': balance_brack += 1
                elif char == ']': balance_brack = max(0, balance_brack - 1)
                elif char == '{': balance_brace += 1
                elif char == '}': balance_brace = max(0, balance_brace - 1)
                
        if current:
            parts.append("".join(current).strip())
        return [p for p in parts if p]

    def process_item(item):
        """Process a single item into a link or text."""
        item = item.strip()
        # Remove leading dash if present (for list items handled manually)
        if item.startswith('- '):
            item = item[2:].strip()
            
        # 1. Check for existing links (HTML, Markdown, Latex \wref/\href)
        # Regex check for markdown link: [text](url)
        if re.search(r'\[.*?\]\(.*?\)', item):
            return item
        # Regex check for HTML anchor
        if re.search(r'<a\s+href', item, re.IGNORECASE):
            return item
        # Regex check for latex links
        if re.match(r'^\s*\\wref', item) or re.match(r'^\s*\\href', item):
            return item
            
        # 2. Check for PDF with description: "foo.pdf (desc)"
        # Simple check: starts with something ending in .pdf
        pdf_match = re.match(r'^(.+?\.pdf)(.*)$', item, re.IGNORECASE)
        if pdf_match:
            filename = pdf_match.group(1).strip()
            rest = pdf_match.group(2)
            # Link the filename, keep the rest as text
            return f'[{filename}](../pdfs/{filename}){rest}'

        # 3. Check for "text (note)" pattern where text is the link target
        # E.g. "stable (∞,1)-category" -> link the whole thing?
        # E.g. "Some concept (see also X)" -> maybe link "Some concept"? 
        # Hard to distinguish. But "models of (∞,1)-categories" is a filename.
        # "see the diagrams of this page" -> "this page" is linked (handled by step 1).
        # If we reached here, it has NO existing links in it.
        
        # If the item seems to be a sentence (contains spaces and maybe no parens-that-look-like-filenames?), 
        # we might just return text.
        # But generally SeeAlso items are links.
        # "models of (∞,1)-categories" -> \wref{models of (∞,1)-categories}
        
        # What if "see the diagrams..." was NOT linked in source? 
        # Then we make the whole thing a link? "see the diagrams...".html? Bad.
        
        # Heuristic: if it's long (> 50 chars?) or looks like a sentence (starts with lowercase?), 
        # maybe don't link it? 
        # But "models of ..." starts with lowercase.
        
        # Let's trust that if the user didn't put a link, they want a [[wikilink]].
        # So \wref{item} is correct for "models of ...".
        
        return f'\\wref{{{item}}}'

    def replace_seealso(match):
        content = match.group(1)
        
        # Check if content looks like a list (has lines starting with -)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        is_list = any(line.startswith('-') for line in lines)
        
        if is_list:
            # Render as <ul>
            items = []
            for line in lines:
                if line.startswith('-'):
                    items.append(process_item(line[1:].strip()))
                else:
                    # Continuation of previous item or just text? 
                    # If it doesn't start with -, maybe append to previous?
                    if items:
                        items[-1] += " " + line
                    else:
                        items.append(line) # Should not happen if correctly formatted
                        
            list_html = "<ul>\n"
            for item in items:
                list_html += f"<li>{item}</li>\n"
            list_html += "</ul>"
            return f'<div class="see-also"><strong>See also:</strong>\n{list_html}</div>'
        else:
            # Inline comma-separated
            items = split_balanced(content)
            links = [process_item(item) for item in items]
            return f'<div class="see-also"><strong>See also:</strong> {", ".join(links)}</div>'

    out_text = []
    idx = 0
    n = len(text)
    while idx < n:
        match = text.find(r'\SeeAlso', idx)
        if match == -1:
            out_text.append(text[idx:])
            break
        
        out_text.append(text[idx:match])
        cur = match + 8 # \SeeAlso
        while cur < n and text[cur].isspace(): cur += 1
        
        if cur < n and text[cur] == '{':
            content, end_pos = parse_balanced(text, cur)
            # Content inside braces
            inner = re.match(r'(.*)', content, re.DOTALL) # use group match to reuse signature if needed or just pass string
            # We need a match object for replace_seealso or just change signature?
            # Let's change signature of replacement logic to take string to be cleaner, 
            # but for minimize diff, I'll wrap it or just call logic directly.
            
            # Refactor replace_seealso to take content string
            # But wait, original code used match.group(1).
            
            # Let's just create a dummy match object or refactor. 
            # Refactoring is better.
            
            # Wait, I cannot easily change the nested function signature in `replace_file_content` 
            # without replacing the whole block.
            # I AM replacing the whole block of `convert_seealso`.
            
            # So I will inline the logic.
            
            # Logic for content:
            # Check if list...
            
            # COPY PASTE LOGIC:
            c = content
            lines = [line.strip() for line in c.split('\n') if line.strip()]
            is_list = any(line.startswith('-') for line in lines)
            
            if is_list:
                items_list = []
                for line in lines:
                    if line.startswith('-'):
                        items_list.append(process_item(line[1:].strip()))
                    else:
                        if items_list:
                            items_list[-1] += " " + line
                        else:
                            items_list.append(line)
                            
                list_str = "<ul>\n"
                for it in items_list:
                    list_str += f"<li>{it}</li>\n"
                list_str += "</ul>"
                replacement = f'<div class="see-also"><strong>See also:</strong>\n{list_str}</div>'
            else:
                its = split_balanced(c)
                lks = [process_item(it) for it in its]
                replacement = f'<div class="see-also"><strong>See also:</strong> {", ".join(lks)}</div>'
                
            out_text.append(replacement)
            idx = end_pos
        else:
            out_text.append(text[match:match+8])
            idx = match + 8
            
    return "".join(out_text)

def convert_citations(text):
    """Convert ((Citation)) to [N] and return (text, references_list)"""
    refs = []
    
    def replace_cite(match):
        content = match.group(1)
        # Check if already in refs
        if content in refs:
            idx = refs.index(content) + 1
        else:
            refs.append(content)
            idx = len(refs)
        return f'<sup><a href="#ref-{idx}">[{idx}]</a></sup>'

    # Match ((...)) but not nested? strict regex
    new_text = re.sub(r'\(\((.*?)\)\)', replace_cite, text)
    return new_text, refs

def wrap_paragraphs(text):
    """Wrap text paragraphs in <p> tags"""
    lines = text.split('\n')
    result = []
    in_tag = False
    in_script = False
    para_buffer = []

    # Tags that should definitely NOT be wrapped in <p>
    BLOCK_TAGS = (
        '<div', '<p', '<script', '<ul', '<ol', '<li', 
        '<h1', '<h2', '<h3', '<h4', '<h5', '<h6', 
        '<table', '<blockquote', '<section', '<header', '<footer', '<style'
    )

    for line in lines:
        stripped = line.strip()

        # Check if we're starting or ending a script/style tag (bypass logic)
        if '<script' in stripped or '<style' in stripped:
            if para_buffer:
                result.append('<p>' + ' '.join(para_buffer) + '</p>')
                para_buffer = []
            in_script = True
            result.append(line)
            if '</script>' in stripped or '</style>' in stripped:
                in_script = False
            continue

        if in_script:
            result.append(line)
            if '</script>' in stripped or '</style>' in stripped:
                in_script = False
            continue

        # Check if line starts with a block tag
        start_is_block = stripped.startswith(BLOCK_TAGS)
        
        # Check if line seems to be a closing block tag (simple heuristic)
        end_is_block = stripped.startswith('</') and (
            stripped.startswith('</div') or stripped.startswith('</ul') or 
            stripped.startswith('</ol') or stripped.startswith('</table')
        )

        if start_is_block or end_is_block:
            # Flush paragraph buffer
            if para_buffer:
                result.append('<p>' + ' '.join(para_buffer) + '</p>')
                para_buffer = []
            result.append(line)
            
            # Simple multi-line tag tracking (imperfect but helps with divs)
            if start_is_block and (not '>' in stripped or stripped.count('<') > stripped.count('>')):
                in_tag = True
            else:
                in_tag = False
        elif in_tag:
            result.append(line)
            if '>' in stripped:
                in_tag = False
        elif stripped == '':
            # Empty line - flush paragraph
            if para_buffer:
                result.append('<p>' + ' '.join(para_buffer) + '</p>')
                para_buffer = []
            result.append(line)
        else:
            # Regular text OR inline tags (<strong>, <a>, etc.) -> add to paragraph
            para_buffer.append(stripped)

    # Flush final paragraph
    if para_buffer:
        result.append('<p>' + ' '.join(para_buffer) + '</p>')

    return '\n'.join(result)

def get_last_modified(tex_path):
    """Get last modified date of the TeX file"""
    if os.path.exists(tex_path):
        mtime = os.path.getmtime(tex_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')

def extract_wikilinks(content):
    """Extract all wikilink targets from LaTeX content"""
    links = set()
    # Match \wref[display]{target} and \wref{target}
    for match in re.finditer(r'\\wref(?:\[[^\]]+\])?\{([^}]+)\}', content):
        target = match.group(1)
        # Remove any PDF anchors (e.g., file.pdf#page=...)
        if '.pdf' in target:
            continue
        links.add(target)
    return sorted(links)

def build_backlinks_map(notes_dir):
    """Build a map of note -> list of notes that link to it"""
    backlinks = {}
    note_files = {}

    # First, get all note files
    for filepath in Path(notes_dir).glob('*.tex'):
        basename = filepath.stem
        note_files[basename] = filepath
        backlinks[basename] = []

    # Now scan each file for links
    for source_name, filepath in note_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            links = extract_wikilinks(content)
            for target in links:
                if target in backlinks:
                    backlinks[target].append(source_name)
        except Exception:
            continue
    return backlinks

def generate_macros(extra_macros=None):
    """Generate KaTeX macros dynamically."""
    # KaTeX macros dict: "\\command": "definition"
    macro_dict = {}
    
    # helper
    def add(k, v):
        # Ensure key starts with \
        key = "\\" + k.lstrip("\\")
        macro_dict[key] = v

    # Add alphabet
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        add(f"c{char}", f"\\mathcal{{{char}}}")
        add(f"bb{char}", f"\\mathbb{{{char}}}")
        add(f"sf{char}", f"\\mathsf{{{char}}}")
        add(f"f{char}", f"\\mathfrak{{{char}}}")
        add(f"b{char}", f"\\mathbf{{{char}}}")
        add(f"s{char}", f"\\mathscr{{{char}}}")
        add(f"e{char}", f"\\mathcal{{{char}}}") 

    # Add small frak
    for char in "abcdefghijklmnopqrstuvwxyz":
        add(f"f{char}", f"\\mathfrak{{{char}}}")
        
    add("bar", "\\overline") # Global override
    
    # Manual additions from style (simplified)
    # Category theory
    add("cC", r"\mathcal{C}")
    add("cD", r"\mathcal{D}")
    add("cF", r"\mathcal{F}")
    add("cG", r"\mathcal{G}")
    add("cH", r"\mathcal{H}")
    add("cL", r"\mathcal{L}")
    add("cM", r"\mathcal{M}")
    add("cP", r"\mathcal{P}")
    add("cU", r"\mathcal{U}")
    add("eF", r"\mathcal{F}")
    add("eU", r"\mathcal{U}")
    add("undC", r"\underline{\mathcal{C}}")
    add("Obj", r"\operatorname{Obj}")
    add("Hom", r"\operatorname{Hom}")
    add("Mor", r"\operatorname{Mor}")
    add("End", r"\operatorname{End}")
    add("Aut", r"\operatorname{Aut}")
    add("id", r"\mathrm{id}")
    add("pt", r"\mathrm{pt}")
    add("Tr", r"\operatorname{Tr}")
    add("eval", r"\operatorname{eval}")
    
    # User (2-Hilbert)
    add("A", r"\operatorname{Sk}")
    add("F", r"\mathcal{F}")
    add("U", r"\mathcal{U}")
    add("orev", r"\overline")
    add("fcj", r"\widehat")
    add("e", r"\varepsilon")
    add("glu", r"\mathrm{gl}")
    add("greyson", r"\bgroup\color{violet}[[#1]]\egroup")
    add("todo", r"\textbf{[[}\textsl{#1}\textbf{]]}")

    # Delimiters (KaTeX doesn't have 'braket' package automatically, define manually)
    add("bkt", r"\left\langle #1 \middle| #2 \right\rangle")
    add("pbkt", r"\left( #1 \middle| #2 \right)")
    add("abs", r"\left| #1 \right|")
    add("norm", r"\left\| #1 \right\|")
    add("set", r"\left\{ #1 \right\}")
    
    # Standard braket emulation
    add("bra", r"\left\langle #1 \right|")
    add("ket", r"\left| #1 \right\rangle")
    add("braket", r"\left\langle #1 \middle| #2 \right\rangle")
    add("set", r"\left\{ #1 \right\}")
    add("Set", r"\left\{ #1 \right\}")

    # Categories
    add("Set", r"\mathbf{Set}")
    add("Grp", r"\mathbf{Grp}")
    add("Top", r"\mathbf{Top}")
    add("Vec", r"\mathbf{Vec}")
    add("Hilb", r"\mathbf{Hilb}")
    add("Sk", r"\operatorname{Sk}")

    # Operators
    add("colim", r"\operatorname{colim}")
    add("Ext", r"\operatorname{Ext}")
    add("Tor", r"\operatorname{Tor}")
    add("Spec", r"\operatorname{Spec}")
    add("im", r"\operatorname{im}")
    add("coker", r"\operatorname{coker}")
    add("coloneqq", r"\mathrel{\vcenter{:}}=")
    add("coloneq", r"\mathrel{\vcenter{:}}=")
    add("eqqcolon", r"=\mathrel{\vcenter{:}}")
    add("endto", r"\to")
    
    # Arrows
    add("to", r"\rightarrow")
    add("injto", r"\hookrightarrow")
    add("surjto", r"\twoheadrightarrow")
    add("longto", r"\longrightarrow")
    add("lto", r"\longrightarrow")
    add("mapsfrom", r"\mathrel{\reflectbox{\ensuremath{\mapsto}}}")
    add("Ising", r"\mathsf{Ising}")
    
    # Greek short
    add("a", r"\alpha")
    add("b", r"\beta")
    add("d", r"\delta")
    add("g", r"\gamma")
    
    # File-specific macros (automatic parsing) - THESE OVERRIDE
    if extra_macros:
        for name, defn in extra_macros.items():
            # Check if it has arguments or is simple
            if isinstance(defn, list):
                # defn is [body, nargs]
                # KaTeX simply uses #1, #2 in the body
                body = defn[0]
                # MathJax used array format, we just need body string with #n
                # We need to ensure backslashes are escaped for JS string
                # Our extract_custom_macros returns raw latex body.
                # However, generate_macros loop (line 1545) ALREADY escapes backslashes.
                # So we must provide raw string here to avoid double escaping.
                add(name, body)
            else: # defn is string body
                add(name, defn)

    # Convert to Javascript object string
    lines = []
    import re
    
    for k, v in macro_dict.items():
        # Key must be quoted string, value must be quoted string or array
        # MathJax 3 macros: keys should NOT have leading backslash
        key = k
        if key.startswith('\\'):
            key = key[1:]
            
        js_key = key
        
        # Check for arguments (#1, #2, etc.)
        # Find the max n in #n, ensuring it's not escaped \#
        # MathJax macro definition string uses #n.
        
        # We need to detect "real" parameters.
        # simple heuristic: look for # followed by digit.
        # But exclude \#.
        
        # Since v is raw latex string (e.g. "\left\langle #1 \right\rangle"),
        # #1 is a param. \# is a literal hash.
        
        matches = re.findall(r'(?<!\\)#(\d)', v)
        max_arg = 0
        if matches:
            max_arg = max(int(m) for m in matches)
            
        # Escape backslashes in value for JS string
        # We need double backslashes for JS string: \rightarrow -> \\rightarrow
        # Also, we need to handle double quotes if present?
        js_val = v.replace('\\', '\\\\').replace('"', '\\"')
        
        if max_arg > 0:
            # Macro with args: ["expansion", num_args]
            lines.append(f'        "{js_key}": ["{js_val}", {max_arg}]')
        else:
            # Simple macro: "expansion"
            lines.append(f'        "{js_key}": "{js_val}"')

    return ",\n".join(lines)

def get_creation_date_from_md(note_name):
    """Try to get creation date from original markdown file."""
    # Search recursively in wiki folder
    wiki_root = Path("/Users/greysonwesley/Desktop/workflow/wiki")
    if not wiki_root.exists():
        return None
        
    # Find file
    # Note: note_name might have special chars usually handled by fs, glob should work
    found = list(wiki_root.rglob(f"{note_name}.md"))
    if not found:
        return None
        
    md_path = found[0]
        
    try:
        content = md_path.read_text(encoding='utf-8')
        # Extract frontmatter
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            fm = match.group(1)
            # Find date: date created: ... or date: ...
            # Prioritize 'date created'
            date_match = re.search(r'^date created:\s*(.+)$', fm, re.MULTILINE | re.IGNORECASE)
            if not date_match:
                 date_match = re.search(r'^date:\s*(.+)$', fm, re.MULTILINE | re.IGNORECASE)
                 
            if date_match:
                raw_full = date_match.group(1).strip()
                # Clean up multiple dates if listed? (YAML list)
                # But regex ^key: value captures one line usually.
                # If it's a list, it starts with newline - .
                # The user's file had 'date modified' as list but 'date created' as single line.
                
                # Handling: August 17, 2025 at 10:09 pm ET
                # Strip ET/CT/MT/PT etc if simplistic
                raw = re.sub(r'\s+[A-Z]{2,3}$', '', raw_full) # Remove timezone suffix
                raw = raw.replace(' at ', ' ') # Remove ' at '
                
                # Check for am/pm and convert to AM/PM for %p
                if 'am' in raw: raw = raw.replace('am', 'AM')
                if 'pm' in raw: raw = raw.replace('pm', 'PM')
                
                formats = [
                    '%B %d, %Y %I:%M %p', # August 17, 2025 10:09 PM
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M',
                    '%Y-%m-%d',
                    '%B %d, %Y %H:%M'
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(raw, fmt)
                        # Format to match Last modified: December 12, 2025 at 10:15 PM ET
                        return dt.strftime('%B %d, %Y at %l:%M %p ET')
                    except ValueError:
                        continue
                        
    except Exception as e:
        print(f"Warning: Failed to parse MD date for {note_name}: {e}")
        return None
    return None

def convert_footnotes(text):
    """Convert \\footnote{...} and [^1] / [^1]: ... to HTML footnotes"""
    
    definitions = {}
    
    # 1. Parse Markdown Footnote Definitions [^id]: content
    # We find line starting with [^id]:
    # We remove them from text and store them
    def extract_md_defs(match):
        fid = match.group(1)
        content = match.group(2).strip()
        definitions[fid] = content
        return "" # Remove definition line
        
    text = re.sub(r'^\[\^([^\]]+)\]:\s*(.*)$', extract_md_defs, text, flags=re.MULTILINE)
    
    # 2. Parse inline LaTeX footnotes \\footnote{content}
    # We replace them with a marker [^auto-N] and add definition
    footnote_counter = 1
    
    def extract_latex_footnote(match):
        nonlocal footnote_counter
        content = match.group(1) # This needs balanced brace parsing technically, relying on existing parser?
        # NO, re.sub is weak with nested braces.
        # But convert_to_html body processing might have stripped unsafe stuff.
        # Let's use a standard robust replacer logic later if needed.
        # For now, simplistic regex.
        fid = f"ftn{footnote_counter}"
        footnote_counter += 1
        definitions[fid] = content
        return f'<sup id="fnref-{fid}"><a href="#fn-{fid}">[{footnote_counter-1 + 1}]</a></sup>'

    # Note: re.sub for \footnote might fail on nested braces. 
    # Use loop with balanced parser for robustness.
    out_text = []
    idx = 0
    while idx < len(text):
        match = text.find(r'\footnote', idx)
        if match == -1:
            out_text.append(text[idx:])
            break
            
        out_text.append(text[idx:match])
        # Find brace
        cur = match + 9 # \footnote
        while cur < len(text) and text[cur].isspace(): cur += 1
        
        if cur < len(text) and text[cur] == '{':
            content, end = parse_balanced(text, cur)
            
            fid = f"auto-{footnote_counter}"
            # Use numeric label for display
            label = str(footnote_counter)
            footnote_counter += 1
            
            definitions[fid] = content
            out_text.append(f'<sup id="fnref-{fid}"><a href="#fn-{fid}">[{label}]</a></sup>')
            idx = end
        else:
            # Failed match
            out_text.append(text[match:match+9])
            idx = match + 9
            
    text = "".join(out_text)

    # 3. Replace Markdown References [^id]
    def replace_md_ref(match):
        fid = match.group(1)
        # Verify we know this def? or just assume it will exist?
        return f'<sup id="fnref-{fid}"><a href="#fn-{fid}">[{fid}]</a></sup>'
        
    text = re.sub(r'\[\^([^\]]+)\](?!:)', replace_md_ref, text)

    # 4. Generate Footer HTML
    if not definitions:
        return text
        
    footer = '\n<div class="footnotes">\n<hr>\n<ol>'
    # Sort definitions?
    # Md definitions by key, Auto definitions by numeric order?
    # Let's just output them.
    # Actually, proper footnotes usually ordered by appearance.
    # Markdown [^ref] order of appearance is good.
    # But dictionary is unordered (pre 3.7) / insertion ordered (3.7+).
    # We just iterate definitions.
    
    for fid, content in definitions.items():
        # Clean content? content might contain markdown or latex.
        # It sits in the footer, so it will be processed by downstream?
        # No, convert_footnotes is called LATE in the pipeline?
        # If called late, content is already processed? 
        # Content extracted from LATE text is already mostly HTML?
        # Actually, if we extract `\footnote{...}` early, content is Latex.
        # If we extract late, it's HTML.
        # We should place this carefuly in pipeline.
        
        # Backlink
        backlink = f' <a href="#fnref-{fid}">↩</a>'
        footer += f'\n<li id="fn-{fid}">{content}{backlink}</li>'
        
    footer += '\n</ol>\n</div>'
    
    return text + footer


def convert_to_html(tex_path, backlinks_map, title_map):
    try:
        content = Path(tex_path).read_text(encoding='utf-8')
    except Exception as e:
        return f"<h1>Error reading file</h1><p>{e}</p>"

    # Strip comments EARLY
    content = strip_comments(content)

    # Metadata
    title, tags = extract_metadata(content)
    # Clean title (use text version of texorpdfstring)
    title = convert_texorpdfstring(title, prefer_text=True)
    
    # Extract macros
    file_macros = extract_custom_macros(content)
    
    body = extract_body(content)

    # Strip known non-semantic commands first
    body = re.sub(r'\\NoteNavigation', '', body)
    body = re.sub(r'\\NoteHeader', '', body)
    body = re.sub(r'\\References', '', body)
    body = re.sub(r'\\Footer', '', body)

    # 2. Convert TikZ and stash scripts (Protect TikZ from escaping)
    body = convert_tikz(body)
    script_blocks = []
    def stash_all_scripts(match):
        script_blocks.append(match.group(0))
        return f'__SCRIPT_BLOCK_{len(script_blocks) - 1}__'
    body = re.sub(r'<script.*?>.*?</script>', stash_all_scripts, body, flags=re.DOTALL)

    # 3. Escape HTML special characters in remaining text (including math)
    body = body.replace('<', '&lt;').replace('>', '&gt;')

    # 4. Convert \defn -> <strong>
    # 4. Convert \defn -> <strong>
    body = replace_command_robust(body, r'\defn', '<strong>{}</strong>')

    # Get note name for metadata lookups
    note_name = Path(tex_path).stem
    name = note_name



    # Load creation dates
    root_dir = Path(__file__).resolve().parent.parent
    metadata_file = root_dir / ".gwiki-metadata.json"

    created_date = "?"
    # 1. Try original Markdown file first
    md_date = get_creation_date_from_md(note_name)
    if md_date:
        created_date = md_date

    # 2. Try metadata file (backup)
    if created_date == "?" and metadata_file.exists():
        try:
            import json
            data = json.loads(metadata_file.read_text())
            c_date_iso = data.get('creation_dates', {}).get(note_name)
            if c_date_iso:
                 # Parse YYYY-MM-DD
                 dt = datetime.strptime(c_date_iso, '%Y-%m-%d')
                 created_date = dt.strftime('%B %d, %Y at %l:%M %p ET')
        except:
            pass
            
    # Fallback to OS creation time if still ?
    if created_date == "?" and os.path.exists(tex_path):
        try:
            # st_birthtime is mac specific, st_ctime is creation on Windows, metadata change on Unix
            # On Mac, st_birthtime exists.
            stat = os.stat(tex_path)
            c_time = getattr(stat, 'st_birthtime', stat.st_ctime) 
            created_date = datetime.fromtimestamp(c_time).strftime('%B %d, %Y at %l:%M %p ET')
        except:
            pass

    if note_name == 'index' and created_date == '?':
        created_date = datetime.now().strftime('%B %d, %Y at %l:%M %p ET')

    # Build compact TOC
    toc_html = ""
    toc_limit = 10
    
    sections = []
    
    # Just modifying the date format for now in this chunk
    # Refine Last Modified
    if os.path.exists(tex_path):
        mtime = os.path.getmtime(tex_path)
        # Format: November 10, 2025 at 9:36 PM ET
        last_modified = datetime.fromtimestamp(mtime).strftime('%B %d, %Y at %l:%M %p ET')
    else:
        last_modified = datetime.now().strftime('%B %d, %Y at %l:%M %p ET')

    # Get outgoing links and backlinks
    outgoing_links = extract_wikilinks(content)
    backlinks = backlinks_map.get(note_name, []) if backlinks_map else []

    # Body conversion pipeline
    # (TikZ conversion and script stashing performed early to handle escaping)

    body = fix_math_colons(body)  # Fix : to \colon in math

    # Stash math blocks to protect from markdown processing
    math_blocks = []
    def stash_math(match):
        math_blocks.append(match.group(0))
        return f'__MATH_BLOCK_{len(math_blocks) - 1}__'

    # Stash math: $$...$$, \[...\], \(...\), $...$
    # First convert $$...$$ to \[...\] (standardize display math)
    body = re.sub(r'\$\$(.*?)\$\$', r'\\[\1\\]', body, flags=re.DOTALL)

    body = re.sub(r'\\\[.*?\\\]', stash_math, body, flags=re.DOTALL)
    body = re.sub(r'\\\((.*?)\\\)', stash_math, body, flags=re.DOTALL)
    # Inline math $...$
    body = re.sub(r'(?<!\\)\$[^$]+(?<!\\)\$', stash_math, body)

    # Convert PDF embeds: ![[file.pdf#page=1&rect=...]]
    def convert_pdf_embed(match):
        link_text = match.group(1)
        # Check for parameters
        if '.pdf' in link_text.lower():
             parts = link_text.split('#')
             filename = parts[0].strip()
             params = ""
             if len(parts) > 1:
                 params = "#" + parts[1]
             
             # Resolve path (assuming PDFs are in ../pdfs/)
             # But wikilinks usually just have filename.
             # Check if file exists in pdf dir?
             pdf_path = f"../pdfs/{filename}"
             
             # Construct embed
             return f'<embed src="{pdf_path}{params}" type="application/pdf" width="100%" height="800px" />'
        
        return match.group(0) # Not a pdf embed, leave for wikilink converter? 
        # Actually wikilink converter handles [[...]], this is ![[...]]
    
    body = convert_seealso(body)
    
    body = re.sub(r'!\[\[(.*?)\]\]', convert_pdf_embed, body)

    body = convert_wikilinks(body, title_map)
    body = convert_markdown_links(body)  # Add markdown link support
    
    # Custom commands
    def convert_arxiv(text):
        """Convert \\arxiv{id} to link"""
        return re.sub(r'\\arxiv\{([^}]+)\}', r'<a href="https://arxiv.org/abs/\1">arXiv:\1</a>', text)

    def strip_incoming_links(text):
        """Remove \\IncomingLinks{...}"""
        return re.sub(r'\\IncomingLinks\{[^}]+\}', '', text)
        
    def convert_nlab(text):
        """Convert \\nlab{keyword} to link"""
        return re.sub(r'\\nlab\{([^}]+)\}', r'<a href="https://ncatlab.org/nlab/show/\1" class="nlab-link">nLab:\1</a>', text)

    def convert_prereq(text, title_map=None):
        """Convert \\prereq{a,b} into a list of links"""
        def replace(match):
            content = match.group(1)
            items = [x.strip() for x in content.split(',')]
            links = []
            for item in items:
                link = item
                if title_map and item in title_map:
                    link = f'<a href="{title_map[item]}">{item}</a>'
                else:
                    # simplistic fallback
                    link = f'<a href="{item}.html">{item}</a>'
                links.append(link)
            return f'<div class="prereq"><strong>Prerequisites:</strong> {", ".join(links)}</div>'
        
        return re.sub(r'\\prereq\{([^}]+)\}', replace, text, flags=re.DOTALL)

    body = convert_arxiv(body)
    body = convert_nlab(body)
    body = convert_prereq(body, title_map)
    body = strip_incoming_links(body)
    
    # DEBUG: Trace disappearing math
    debug_marker = "Integrating both sides from"
    if debug_marker in body:
        print(f"[DEBUG] Pre-formatting: {body[body.find(debug_marker):body.find(debug_marker)+100]}")

    body = convert_bold(body)
    # Use robust method for textbf, emph, textit, texttt
    body = replace_command_robust(body, r'\textbf', '<strong>{}</strong>')
    body = replace_command_robust(body, r'\emph', '<em>{}</em>')
    body = convert_italic(body)
    body = convert_quotes(body)          # Add smart quotes support
    body = replace_command_robust(body, r'\textit', '<em>{}</em>')
    body = replace_command_robust(body, r'\texttt', '<code>{}</code>')
    body = replace_command_robust(body, r'\greyson', '<span style="color: #7f00ff;">[[{}]]</span>')
    body = replace_command_robust(body, r'\todo', '<strong>[[<em>{}</em>]]</strong>')
    body = convert_specialchars(body)    # Handle \textbackslash etc.
    
    if debug_marker in body:
        print(f"[DEBUG] Post-formatting: {body[body.find(debug_marker):body.find(debug_marker)+100]}")
    
    # Remove \allformats{...}
    body = re.sub(r'\\allformats\{[^}]+\}', '', body)

    # Convert texorpdfstring early
    body = convert_texorpdfstring(body)
    
    # Handle citations
    body, references = convert_citations(body)
    
    # Restore math blocks (processed in reverse order to handle nested stash)
    for i, block in reversed(list(enumerate(math_blocks))):
        body = body.replace(f'__MATH_BLOCK_{i}__', block)
    
    if debug_marker in body:
        print(f"[DEBUG] Post-restoration: {body[body.find(debug_marker):body.find(debug_marker)+100]}")

    body = convert_lst(body)           # Handle LaTeX lists (Moved before environments!)
    body = convert_itemize(body)       # Handle markdown lists
    body = convert_environments(body)  # Environments now see HTML lists
    body = convert_textit(body)        # Handle \textit
    body = convert_itemize(body)       # Handle markdown lists
    body = convert_environments(body)  # Environments now see HTML lists
    body = convert_sections(body)
    
    body = convert_labels(body)
    body = convert_refs(body)
    body = convert_href(body)
    

    body = convert_footnotes(body)
    
    # Convert center environment (do this late to avoid interfering with other blocks)
    # Match \begin{center} ... \end{center}
    body = re.sub(r'\\begin\{center\}(.*?)\\end\{center\}', r'<div style="text-align: center;">\1</div>', body, flags=re.DOTALL)

    # Append References if any
    if references:
        body += '\n<div class="references">\n<h2>References</h2>\n<ol>\n'
        for i, ref in enumerate(references, 1):
             body += f'<li id="ref-{i}">{ref}</li>\n'
        body += '</ol>\n</div>'

    # Restore scripts
    for i, block in enumerate(script_blocks):
        body = body.replace(f'__SCRIPT_BLOCK_{i}__', block)

    body = wrap_paragraphs(body)

    # Extract sections for table of contents
    sections = re.findall(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', body)
    
    # Macros generated dynamically



    # Clean title
    title = convert_texorpdfstring(title)

    # Generate HTML
    html_parts = []
    html_parts.append(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - GWiki</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="style.css">
    <link rel="stylesheet" type="text/css" href="https://tikzjax.com/v1/fonts.css">
    <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        macros: {{
{generate_macros(file_macros)}
        }}
      }},
      startup: {{
        typeset: true
      }}
    }};
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script src="https://tikzjax.com/v1/tikzjax.js"></script>
</head>
<body>
    <div class="top-nav">
        <div class="nav-left">
            <a href="../index.html" class="nav-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 12H5M12 19l-7-7 7-7"/>
                </svg>
                <span>Index</span>
            </a>
        </div>
        <div class="nav-right">
            <a href="../pdfs/{name}.pdf" class="nav-btn" title="View PDF">
                <span>PDF</span>
            </a>
            <a href="obsidian://open?path=/Users/greysonwesley/Desktop/workflow/wiki/{name}.md" class="nav-btn" title="Edit in Obsidian">
                <span>MD</span>
            </a>
        </div>
    </div>
    <div class="content-wrapper">
    <h1>{title}</h1>
    <div class="metadata">
        <strong>Last modified:</strong> {last_modified}<br>
        <strong>Created:</strong> {created_date}<br>''')

    if tags:
        html_parts.append(f'''
        <strong>Tags:</strong> {", ".join(tags)}''')

    html_parts.append('''
    </div>''')
    
    html = "".join(html_parts)

    # Generate TOC HTML if sections exist
    toc_html = ""
    if sections and len(sections) > 1:
        toc_html = '''
        <div class="toc-compact">
            <h3>Contents</h3>
            <ul>'''
        for header_id, title in sections:
            toc_html += f'''
                <li><a href="#{header_id}">{title}</a></li>'''
        toc_html += '''
            </ul>
        </div>'''

    # Add anchors to sections in body (REMOVED - convert_sections does this)

    html += f'''
    <div class="content">
        {toc_html}
        {body}
    </div>'''

    # Add linked notes section if there are outgoing links
    if outgoing_links:
        html += '''

    <div class="linked-notes">
        <h2>Linked Notes</h2>
        <ul>'''
        for link in outgoing_links:
            html += f'''
            <li><a href="{link}.html">{link}</a></li>'''
        html += '''
        </ul>
    </div>'''

    # Add backlinks section if there are any
    if backlinks:
        html += '''

    <div class="backlinks">
        <h2>Backlinks</h2>
        <ul>'''
        for backlink in sorted(backlinks):
            html += f'''
            <li><a href="{backlink}.html">{backlink}</a></li>'''
        html += '''
        </ul>
    </div>'''

    html += '''
    </div>
</body>
</html>
'''

    return html

def main():
    if len(sys.argv) < 2:
        print("Usage: tex-to-html.py <input.tex> [output.html]")
        sys.exit(1)

    tex_path = sys.argv[1]

    if not os.path.exists(tex_path):
        print(f"Error: {tex_path} not found")
        sys.exit(1)

    # Security Check: Respect % noconvert directive
    try:
        with open(tex_path, 'r', encoding='utf-8') as f:
            # Read first 1024 bytes (sufficient for header)
            chunk = f.read(1024)
            if re.search(r'%\s*(noconvert|nochange)', chunk, re.IGNORECASE):
                print(f"Skipping {tex_path}: marked as % noconvert")
                return
    except Exception as e:
        print(f"Warning: Could not read {tex_path} for noconvert check: {e}")

    # Determine output path
    if len(sys.argv) >= 3:
        html_path = sys.argv[2]
    else:
        # Default: input.tex -> html/input.html
        basename = os.path.splitext(os.path.basename(tex_path))[0]
        html_path = os.path.join('html', f'{basename}.html')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(html_path) or '.', exist_ok=True)

    # Build backlinks map from notes directory
    notes_dir = os.path.dirname(tex_path) or 'notes'
    backlinks_map = build_backlinks_map(notes_dir)
    title_map = build_title_map(notes_dir)

    # Convert
    html = convert_to_html(tex_path, backlinks_map, title_map)

    # Write output
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Converted: {tex_path} -> {html_path}")

if __name__ == '__main__':
    main()
