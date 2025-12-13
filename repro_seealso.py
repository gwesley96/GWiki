
import re
import sys
import os

# Mock the parts of tex-to-html.py needed
def parse_balanced(text, start_pos, open_char='{', close_char='}'):
    depth = 0
    escaped = False
    for i in range(start_pos, len(text)):
        char = text[i]
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start_pos+1:i], i + 1
    return text[start_pos+1:], len(text)

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
        return f'\\wref{{{item}}}'

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

# Test case
latex_snippet = r"""
\SeeAlso{
- models of (∞,1)-categories
- ∞-category of spaces
- ∞-category of spectra
- stable (∞,1)-category
- [Elements of ∞-category theory](https://emilyriehl.github.io/files/elements.pdf) (Riehl–Verity)
- see the diagrams of [this page](https://ncatlab.org/nlab/show/Lie+n-groupoid)
- icats.pdf (a fantastic set of notes)
}
"""

converted = convert_seealso(latex_snippet)
print(converted)
