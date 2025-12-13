import re

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
        cur = match + 14 # len('\texorpdfstring')
        
        # Skip space?
        while cur < n and text[cur].isspace(): cur += 1
            
        # Parse 1st arg (TEX)
        if cur < n and text[cur] == '{':
            balance = 1
            i_start = cur + 1
            cur += 1
            while cur < n and balance > 0:
                if text[cur] == '{': balance += 1
                elif text[cur] == '}': balance -= 1
                cur += 1
            tex_content = text[i_start:cur-1]
        else:
            # Error or malformed
            out.append(text[match:match+14]) # restore command
            i = match + 14
            continue
            
        # Parse 2nd arg (PDF)
        while cur < n and text[cur].isspace(): cur += 1
        if cur < n and text[cur] == '{':
             balance = 1
             i_start = cur + 1
             cur += 1
             while cur < n and balance > 0:
                if text[cur] == '{': balance += 1
                elif text[cur] == '}': balance -= 1
                cur += 1
        else:
             # Malformed
             out.append(text[match:match+14])
             i = match + 14
             continue
             
        out.append(tex_content)
        i = cur
        
    result = "".join(out)
    return result.replace('\n', ' ').strip()

def test_math_stash(text):
    math_blocks = []
    def stash_math(match):
        math_blocks.append(match.group(0))
        return f'__MATH_BLOCK_{len(math_blocks) - 1}__'

    # Inline math $...$
    # NOTE: The original script uses default flags (No DOTALL) for inline math
    text = re.sub(r'(?<!\\)\$[^$]+(?<!\\)\$', stash_math, text)
    
    print("Stashed Text:", text)
    print("Blocks:", math_blocks)

    # Simulate restoration
    for i, block in enumerate(math_blocks):
        text = text.replace(f'__MATH_BLOCK_{i}__', block)
    return text

print("--- Test 1: Texorpdfstring with newline ---")
input_header = r"Special cases of \texorpdfstring{$\mathcal{P" + "\n" + r"\exp$}{Pexp}}"
print("Input:", input_header)
print("Output:", convert_texorpdfstring(input_header))

print("\n--- Test 2: Inline math with t_1 ---")
input_math = r"Integrating both sides from $t_1=0$ to $t_1=t$, we find"
print("Input:", input_math)
output_math = test_math_stash(input_math)
print("Restored:", output_math)
if "$t_1=0$" not in output_math:
    print("FAIL: Math disappeared!")
else:
    print("SUCCESS: Math preserved.")
