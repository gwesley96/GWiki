from pathlib import Path
import re

def parse_metadata(content):
    meta = {'title': None}
    if '\\Title{' in content:
        start = content.find('\\Title{') + 7
        balance = 1
        i = start
        while i < len(content) and balance > 0:
            if content[i] == '{': balance += 1
            elif content[i] == '}': balance -= 1
            i += 1
        if balance == 0:
            meta['title'] = content[start:i-1]
    return meta

path = "notes/2-Hilbert spaces give Hstar-algebras.tex"
content = Path(path).read_text(encoding='utf-8')
print("Original Title Line:", re.search(r'\\Title.*', content).group(0))
meta = parse_metadata(content)
print("Extracted Title:", meta['title'])

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
        cur = match + 14
        while cur < n and text[cur].isspace(): cur += 1
        
        # Parse 1st arg
        if cur < n and text[cur] == '{':
            balance = 1
            start = cur + 1
            cur += 1
            while cur < n and balance > 0:
                if text[cur] == '{': balance += 1
                elif text[cur] == '}': balance -= 1
                cur += 1
            tex_content = text[start:cur-1]
        else:
            i = match+14
            continue

        # Parse 2nd arg
        while cur < n and text[cur].isspace(): cur += 1
        if cur < n and text[cur] == '{':
             balance = 1
             start = cur + 1
             cur += 1
             while cur < n and balance > 0:
                if text[cur] == '{': balance += 1
                elif text[cur] == '}': balance -= 1
                cur += 1
        else:
             i = match+14
             continue

        out.append(tex_content)
        i = cur
    return "".join(out)

print("Cleaned Title:", convert_texorpdfstring(meta['title']))
