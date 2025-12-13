
import re

def parse_balanced(text, start_index):
    """
    Parse a balanced curly brace group starting at start_index (pointing to '{').
    Returns (content, end_index) where end_index is the index AFTER the closing '}'.
    """
    if start_index >= len(text) or text[start_index] != '{':
        return "", start_index
    
    depth = 0
    i = start_index
    n = len(text)
    
    while i < n:
        char = text[i]
        
        # Check for escaped braces
        if char == '\\':
            i += 2
            continue
            
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                # Found the matching closing brace
                return text[start_index+1 : i], i + 1
        
        i += 1
        
    # If we get here, braces are unbalanced
    return text[start_index+1:], n

def convert_texorpdfstring(text):
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
             
        # Clean the TEX content using logic from implementation
        clean_content = tex_content # removed stripping for now to match behavior
        out.append(clean_content)
        i = cur
        
    return "".join(out)

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
            # BUT WAIT: cmd_len includes the brace or *?
            # if *, cmd_len is 1+len+1.
            # but if it was matched, we expect braces.
            # if we fail to find brace, we should just append command.
            i += 1 + len(cmd) # risky if *
            continue
            
    # Markdown headers (Keep regex for simple markdown)
    text = "".join(out)
    return text

# Test case
input_tex = r"Some text before. \section*{Special cases of \texorpdfstring{$\mathcal{P}\exp$}{Pexp}} Some text after."
print(f"Input: {input_tex}")

step1 = convert_texorpdfstring(input_tex)
print(f"Step 1 (TexOrPdf): {step1}")

step2 = convert_sections(step1)
print(f"Step 2 (Sections): {step2}")
