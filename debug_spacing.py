
import re
import sys

def protect_math(text):
    tokens = []
    def replace_func(match):
        token = f"__MATH_TOKEN_{len(tokens)}__"
        tokens.append(match.group(0))
        return token
    text = re.sub(r'(?s)\$\$.*?\$\$', replace_func, text)
    text = re.sub(r'(?<!\\)\$(?:\\.|[^$])+\$(?!\d)', replace_func, text)
    return text, tokens

def restore_math(text, tokens):
    for i, token in enumerate(tokens):
        placeholder = f"__MATH_TOKEN_{i}__"
        idx = text.find(placeholder)
        if idx == -1: continue
        prefix = ""
        if idx > 0:
            c = text[idx-1]
            if (c.isalnum() or c in ')}],.') and not c.isspace():
                prefix = " "
        suffix = ""
        end_idx = idx + len(placeholder)
        if end_idx < len(text):
            c = text[end_idx]
            if c.isalnum() and not c.isspace():
                suffix = " "
        text = text.replace(placeholder, prefix + token + suffix)
    return text

def clean_math(text):
    text = re.sub(r'(?<!\\)\$(\s+)?((?:\\.|[^$])+?)(\s+)?\$(?!\d)', r'$\2$', text)
    return text

# Test case from the user's issue (using converted macros)
input_text = r"functions on $\cE$ into $B(\cH)$ with"
print(f"Original: '{input_text}'")

# COPY OF clean_math FROM LINE 416
def clean_math(text):
    text = re.sub(r'(?<!\\)\$(\s+)?((?:\\.|[^$])+?)(\s+)?\$(?!\d)', r'$\2$', text)
    return text

print(f"Cleaned: '{clean_math(input_text)}'")
