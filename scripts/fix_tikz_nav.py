
import os
import re
from pathlib import Path

NOTES_DIR = Path('notes')

# 1. Identify valid files
# Stubs are already deleted, so we can trust what remains, but let's double check size just in case
files = sorted([f for f in os.listdir(NOTES_DIR) if f.startswith('tikz test') and f.endswith('.tex')])
valid_map = {} 

pattern = re.compile(r'tikz test (\d+)(.*)\.tex')

for f in files:
    match = pattern.match(f)
    if match:
        num = int(match.group(1))
        # Ensure it's not a re-generated tiny file if any remain (though I deleted them)
        if (NOTES_DIR / f).stat().st_size > 300:
            valid_map[num] = f[:-4]

print("Updating navigation...")
nums = sorted(valid_map.keys())

for i, num in enumerate(nums):
    filename = valid_map[num]
    filepath = NOTES_DIR / f"{filename}.tex"
    
    prev_ref = valid_map[nums[i-1]] if i > 0 else None
    next_ref = valid_map[nums[i+1]] if i < len(nums) - 1 else None
    
    # Construct nav string
    nav_line = "Navigation: "
    if prev_ref:
        nav_line += f"\\wref{{{prev_ref}}} (previous)"
    else:
        nav_line += "(no previous)"
    
    nav_line += " | "
    
    if next_ref:
        nav_line += f"\\wref{{{next_ref}}} (next)"
    else:
        nav_line += "(no next)"
        
    content = filepath.read_text()
    
    # Check if Navigation line exists
    if "Navigation:" in content:
        # Use lambda to avoid escape issues in replacement string
        content = re.sub(r'Navigation:.*', lambda m: nav_line, content)
        filepath.write_text(content)
        print(f"  Updated {filename}")
    else:
        print(f"  Skipped {filename} (no Navigation line)")

print("Done.")
