import re

text = r"""
\textbf{Definition.} An (unenriched, $H$-pivotal) \textbf{disk-like $n$-category} $\mathcal{C}$ consists of the following data.
* For each...
"""

# Test Clean Math
text_math = r"word$math$ and $ H $ and (unenriched,$H$-pivotal)"
def clean_math(text):
    # Remove extra spacing inside inline math: $ H $ -> $H$
    text = re.sub(r'(?<!\\)\$\s+([^$]+?)\s+\$(?!\d)', r'$\1$', text)
    text = re.sub(r'(?<!\\)\$\s+([^$]+?)\$(?!\d)', r'$\1$', text)
    text = re.sub(r'(?<!\\)\$([^$]+?)\s+\$(?!\d)', r'$\1$', text)
    
    # Add spacing around inline math: word$math$ -> word $math$
    text = re.sub(r'([a-zA-Z0-9,\.])\$(?=[^$])', r'\1 $', text) # char followed by $
    text = re.sub(r'(?<=[^$])\$([a-zA-Z0-9])', r'$ \1', text)   # $ followed by char
    
    # Fix double spaces if any created
    text = text.replace('  $', ' $').replace('$  ', '$ ')
    return text

print("Math Original:", text_math)
print("Math Cleaned: ", clean_math(text_math))

# Test Theorem
thm = "Definition"
pattern = r'\\textbf\{' + thm + r'\.\}\s*(.*?)(?=\n\n|\Z)'
def repl_thm(match):
    return "MATCHED_DEFINITION"

print("\nRegex pattern:", pattern)
match = re.search(pattern, text, flags=re.DOTALL)
if match:
    print("Theorem Matched!")
    print("Group 1:", match.group(0))
else:
    print("Theorem NOT Matched")
