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
    title_match = re.search(r'\\Title\{([^}]+)\}', content)
    tags_match = re.search(r'\\Tags\{([^}]*)\}', content)

    title = title_match.group(1) if title_match else "Untitled"
    tags_raw = tags_match.group(1) if tags_match else ""
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()]

    return title, tags

def extract_body(content):
    r"""Extract content between \NoteHeader and \References"""
    # Find content between \NoteHeader and one of: \References, \Footer, \end{document}
    # But need to handle \end{document} inside code blocks
    # Strategy: First extract from \NoteHeader to the first \References or \Footer
    # If those don't exist, go to \end{document} but skip any inside ```...```

    # Try \References or \Footer first (these are unambiguous)
    match = re.search(r'\\NoteHeader\s*(.*?)(?=\\References\b|\\Footer\b)', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no \References or \Footer, extract to the OUTER \end{document}
    # (not one inside a code block)
    match = re.search(r'\\NoteHeader\s*(.*)', content, re.DOTALL)
    if match:
        body = match.group(1)
        # Find the last \end{document} (the outer one)
        last_end = body.rfind(r'\end{document}')
        if last_end != -1:
            return body[:last_end].strip()
        return body.strip()

    # Fallback: Extraction between \begin{document} and \end{document}
    match = re.search(r'\\begin\{document\}(.*)', content, re.DOTALL)
    if match:
        body = match.group(1)
        last_end = body.rfind(r'\end{document}')
        if last_end != -1:
            return body[:last_end].strip()
        return body.strip()

    return ""

def convert_wikilinks(text):
    """Convert \wref links to HTML links (supports optional display moved before or after)."""
    def repl(match):
        display = match.group('display') or match.group('display_after') or match.group('target')
        target = match.group('target')
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
    # Be careful not to match ** patterns or single * that are terminal objects
    # Only match *word* patterns, not standalone *
    text = re.sub(r'(?<!\*)\*(?!\*)([a-zA-Z][^*]+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    return text

def convert_tikz(text):
    """Convert tikz code blocks, inline tikzcd, tkz environment, and \tz command to TikZJax."""
    
    # helper to stash content to protect from regexes
    verb_blocks = []
    def stash_verb(match):
        verb_blocks.append(match.group(0))
        return f'__VERB_BLOCK_{len(verb_blocks) - 1}__'

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

    # 3. Handle \tz[opt]{content}
    def repl_tz(match):
        opt = match.group(1) if match.group(1) else ""
        content = match.group(2)
        tikz_code = f'\\begin{{tikzpicture}}[{opt}]\n{content}\n\\end{{tikzpicture}}'
        return stash_script(wrap_tikz(tikz_code))
        
    text = re.sub(r'\\tz(?:\[([^\]]*)\])?\{((?:[^{}]|{[^{}]*})*)\}', repl_tz, text, flags=re.DOTALL)

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

        # Remove \label{...} commands
        body = re.sub(r'\\label\{[^}]+\}', '', body)

        # Handle optional argument (usually the title)
        title = ""
        # Special case for Idea: if optional is "Idea", don't repeat it.
        if env_name == "idea" and optional == "Idea":
             title = f"<strong>{env_name.capitalize()}.</strong>"
        elif optional:
            title = f"<strong>{env_name.capitalize()} ({optional}).</strong>"
        else:
            title = f"<strong>{env_name.capitalize()}.</strong>"

        # Content placement logic
        # If body starts with a list (<ul> or <ol>), title goes on separate line/paragraph
        if body.startswith('<ul>') or body.startswith('<ol>'):
             content = f'<p>{title}</p>\n{body}'
        else:
             # Inline title - we rely on wrap_paragraphs to keep this together if it's text
             content = f'{title} {body}'

        return f'<div class="{env_name}">\n{content}\n</div>'

    # Match \begin{env}[optional]{body}\end{env} or \begin{env}{body}\end{env}
    text = re.sub(
        r'\\begin\{(definition|theorem|lemma|proposition|corollary|example|remark|idea)\}(?:\[([^\]]+)\])?(.*?)\\end\{\1\}',
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
        content = match.group(1)
        # Split by \item
        items = re.split(r'\s*\\item\s+', content)
        # Filter empty items
        items = [item.strip() for item in items if item.strip()]
        
        list_html = "<ul>\n"
        for item in items:
            list_html += f"<li>{item}</li>\n"
        list_html += "</ul>"
        return list_html

    text = re.sub(r'\\begin\{lst\}(.*?)\\end\{lst\}', replace_lst, text, flags=re.DOTALL)
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
    """Convert markdown-style headers and LaTeX sections to HTML"""
    # LaTeX sections
    text = re.sub(r'\\section\*?\{([^}]+)\}', r'<h2>\1</h2>', text)
    text = re.sub(r'\\subsection\*?\{([^}]+)\}', r'<h3>\1</h3>', text)
    text = re.sub(r'\\subsubsection\*?\{([^}]+)\}', r'<h4>\1</h4>', text)

    # Markdown headers
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
    """Convert \SeeAlso command"""
    def replace_seealso(match):
        content = match.group(1)
        # Split by comma
        items = [item.strip() for item in content.split(',')]
        # Convert to links
        links = [f'<a href="{item}.html">{item}</a>' for item in items]
        return f'<p><strong>See also:</strong> {", ".join(links)}</p>'

    text = re.sub(r'\\SeeAlso\{([^}]+)\}', replace_seealso, text)
    return text

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

def convert_to_html(tex_path, backlinks_map=None):
    """Main conversion function"""
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    title, tags = extract_metadata(content)
    body = extract_body(content)

    # Get note name for metadata lookups
    note_name = Path(tex_path).stem

    # Load creation dates
    root_dir = Path(__file__).resolve().parent.parent
    metadata_file = root_dir / ".gwiki-metadata.json"
    created_date = "?"
    if metadata_file.exists():
        try:
            import json
            data = json.loads(metadata_file.read_text())
            created_date = data.get('creation_dates', {}).get(note_name, "?")
        except:
            pass

    # Refine Last Modified
    if os.path.exists(tex_path):
        mtime = os.path.getmtime(tex_path)
        last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    else:
        last_modified = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Get outgoing links and backlinks
    outgoing_links = extract_wikilinks(content)
    backlinks = backlinks_map.get(note_name, []) if backlinks_map else []

    # Convert body
    # Important: Do tikz/bold/italic/wikilinks BEFORE environments
    # to avoid issues with nested conversions
    body = convert_tikz(body)

    # Stash scripts to protect them from wikilinks and other regexes
    script_blocks = []
    def stash_all_scripts(match):
        script_blocks.append(match.group(0))
        return f'__SCRIPT_BLOCK_{len(script_blocks) - 1}__'
    
    body = re.sub(r'<script.*?>.*?</script>', stash_all_scripts, body, flags=re.DOTALL)

    body = fix_math_colons(body)  # Fix : to \colon in math
    body = convert_wikilinks(body)
    body = convert_bold(body)
    body = convert_latex_bold(body) # Add \textbf support
    body = convert_italic(body)
    body = convert_lst(body)           # Handle LaTeX lists (Moved before environments!)
    body = convert_itemize(body)       # Handle markdown lists
    body = convert_environments(body)  # Environments now see HTML lists
    body = convert_sections(body)
    body = convert_seealso(body)
    
    # Convert center environment (do this late to avoid interfering with other blocks)
    # Match \begin{center} ... \end{center}
    body = re.sub(r'\\begin\{center\}(.*?)\\end\{center\}', r'<div style="text-align: center;">\1</div>', body, flags=re.DOTALL)

    # Restore scripts
    for i, block in enumerate(script_blocks):
        body = body.replace(f'__SCRIPT_BLOCK_{i}__', block)

    body = wrap_paragraphs(body)

    # Extract sections for table of contents
    sections = re.findall(r'<h2>(.*?)</h2>', body)

    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - GWiki</title>
    <link rel="stylesheet" type="text/css" href="https://tikzjax.com/v1/fonts.css">
    <script>
    window.MathJax = {{
        tex: {{
            inlineMath: [['$', '$']],
            displayMath: [['\\\\[', '\\\\]']],
            macros: {{
                // Category theory
                cC: '\\\\mathcal{{C}}',
                cD: '\\\\mathcal{{D}}',
                cF: '\\\\mathcal{{F}}',
                cG: '\\\\mathcal{{G}}',
                cH: '\\\\mathcal{{H}}',
                cL: '\\\\mathcal{{L}}',
                cM: '\\\\mathcal{{M}}',
                cP: '\\\\mathcal{{P}}',
                cU: '\\\\mathcal{{U}}',
                Obj: '\\\\operatorname{{Obj}}',
                Hom: '\\\\operatorname{{Hom}}',
                Mor: '\\\\operatorname{{Mor}}',
                End: '\\\\operatorname{{End}}',
                Aut: '\\\\operatorname{{Aut}}',
                id: '\\\\mathrm{{id}}',

                // Blackboard bold
                bR: '\\\\mathbb{{R}}',
                bC: '\\\\mathbb{{C}}',
                bZ: '\\\\mathbb{{Z}}',
                bN: '\\\\mathbb{{N}}',
                bQ: '\\\\mathbb{{Q}}',

                // Categories
                Set: '\\\\mathbf{{Set}}',
                Grp: '\\\\mathbf{{Grp}}',
                Top: '\\\\mathbf{{Top}}',
                Vec: '\\\\mathbf{{Vec}}',

                // Operators
                colim: '\\\\operatorname{{colim}}',
                Ext: '\\\\operatorname{{Ext}}',
                Tor: '\\\\operatorname{{Tor}}',
                Spec: '\\\\operatorname{{Spec}}',
                im: '\\\\operatorname{{im}}',
                coker: '\\\\operatorname{{coker}}',
                coloneqq: '\\\\mathrel{{\\\\vcenter{{:}}}}=',
                coloneq: '\\\\mathrel{{\\\\vcenter{{:}}}}=',

                // TikZ-like (limited in HTML)
                to: '\\\\rightarrow',
                injto: '\\\\hookrightarrow',
                surjto: '\\\\twoheadrightarrow'
            }}
        }}
    }};
    </script>
    <script src="https://tikzjax.com/v1/tikzjax.js"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0;
            font-family: Georgia, serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
        }}
        .top-nav {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .top-nav a {{
            color: white;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
        }}
        .top-nav a:hover {{
            text-decoration: underline;
        }}
        .content-wrapper {{
            background: white;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 40px 60px 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }}
        h1 {{
            color: #2563eb;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #1e40af;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #1e3a8a;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        h4 {{
            color: #1e40af;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .metadata {{
            font-size: 0.85em;
            color: #6b7280;
            margin-bottom: 25px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
        }}
        .toc {{
            background: #f0f9ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
        }}
        .toc h3 {{
            margin-top: 0;
            color: #1e40af;
            font-size: 1.1em;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 0;
            margin: 10px 0 0 0;
        }}
        .toc li {{
            margin: 5px 0;
        }}
        .toc a {{
            color: #2563eb;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .topics {{
            background: #f3f4f6;
            padding: 15px;
            border-left: 4px solid #2563eb;
            margin: 20px 0;
        }}
        .idea {{
            background: #ecfeff;
            border: 1px solid #06b6d4;
            border-left: 4px solid #06b6d4;
            padding: 4px 8px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .definition, .theorem, .example, .lemma, .proposition, .corollary, .remark {{
            margin: 20px 0;
            padding: 8px;
            border-radius: 4px;
        }}
        .definition p, .theorem p, .example p, .lemma p, .proposition p, .corollary p, .remark p, .idea p {{
            margin: 0;
        }}
        .definition {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }}
        .theorem, .lemma, .proposition, .corollary {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
        }}
        .example {{
            background: #f3e8ff;
            border-left: 4px solid #a855f7;
        }}
        .remark {{
            background: #f3f4f6;
            border-left: 4px solid #6b7280;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        script[type="text/tikz"] {{
            /* display: block; - Hiding this to prevents raw code from showing if TikZJax fails */
            margin: 20px 0;
            text-align: center;
        }}
        svg {{
            display: block;
            margin: 20px auto;
            max-width: 100%;
        }}
        .linked-notes, .backlinks {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
        .linked-notes h2, .backlinks h2 {{
            color: #1e40af;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .linked-notes ul, .backlinks ul {{
            list-style: none;
            padding-left: 0;
        }}
        .linked-notes li, .backlinks li {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="top-nav">
        <a href="../index.html">← Back to Index</a>
    </div>
    <div class="content-wrapper">
    <h1>{title}</h1>
    <div class="metadata">
        <strong>Last modified:</strong> {last_modified}<br>
        <strong>Created:</strong> {created_date}<br>'''

    if tags:
        html += f'''
        <strong>Tags:</strong> {", ".join(tags)}'''

    html += f'''
    </div>'''

    # Add table of contents if sections exist
    if sections and len(sections) > 2:
        html += '''
    <div class="toc">
        <h3>Contents</h3>
        <ul>'''
        for section in sections:
            # Create anchor from section title
            anchor = re.sub(r'[^a-z0-9]+', '-', section.lower()).strip('-')
            html += f'''
            <li><a href="#{anchor}">{section}</a></li>'''
        html += '''
        </ul>
    </div>'''

    # Add anchors to sections in body
    if sections and len(sections) > 2:
        for section in sections:
            anchor = re.sub(r'[^a-z0-9]+', '-', section.lower()).strip('-')
            body = body.replace(f'<h2>{section}</h2>', f'<h2 id="{anchor}">{section}</h2>')

    html += f'''

    <div class="content">
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

    # Convert
    html = convert_to_html(tex_path, backlinks_map)

    # Write output
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Converted: {tex_path} -> {html_path}")

if __name__ == '__main__':
    main()
