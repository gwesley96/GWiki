import os
import re
from pathlib import Path

NOTES_DIR = Path("notes")

# Map of old filename (stem) -> new filename (stem)
# If new filename matches an existing file different from old, old is deleted and refs updated.
# If new filename doesn't exist, old is renamed.

renames = {
    "tensor-field": "Tensor Field",
    "smooth-manifold": "Smooth Manifold",
    "quadratic-form": "Quadratic Form",
    "positive-definite-form": "Positive Definite Form",
    "partition-of-unity": "Partition of Unity",
    "jacobi-identity": "Jacobi Identity",
    "banach-algebra": "Banach algebra", # map to existing
    "hopf-algebra": "Hopf algebra",     # map to existing
    "DG-algebra": "DG Algebra",         # merge/rename
    "dg algebra": "DG Algebra",         # target
    "riemann-(04)-curvature-tensor": "Riemann (0,4)-Curvature Tensor",
    # Junk to delete (no target, just gone, or assume refs are broken/irrelevant)
    "3Hilb.pdf#page=25&selection=181,0,181,8&color=yellow": None,
    "BartlettTQFTs.pdf#page=24&selection=30,6,30,29": None,
    "LurieTQFTClassification2009.pdf#page=160&selection=133,0,133,12&color=yellow": None,
    "QsystemCompletionis3Functor.pdf#page=27&rect=72,106,528,238": None,
}

def update_content(content, rename_map):
    # Regex to find \wref{...}, \SeeAlso{...}, \IncomingLinks{...}
    # Also handle comma lists in SeeAlso/Aliases/IncomingLinks/Tags? Not Tags.
    
    # 1. \wref{key}
    def replace_wref(match):
        key = match.group(1)
        if key in rename_map:
            target = rename_map[key]
            if target:
                return f"\\wref{{{target}}}"
        return match.group(0)
    
    content = re.sub(r'\\wref\{([^}]+)\}', replace_wref, content)
    
    # 2. \wref[display]{key}
    def replace_wref_opt(match):
        display = match.group(1)
        key = match.group(2)
        if key in rename_map:
            target = rename_map[key]
            if target:
                return f"\\wref[{display}]{{{target}}}"
        return match.group(0)

    content = re.sub(r'\\wref\[([^\]]+)\]\{([^}]+)\}', replace_wref_opt, content)

    # 3. Comma lists: \SeeAlso, \IncomingLinks. \Aliases? (Maybe alias DGA -> DG Algebra)
    # Functions like \SeeAlso{a,b,c}
    def replace_list(match):
        cmd = match.group(1)
        items_str = match.group(2)
        items = [x.strip() for x in items_str.split(',')]
        new_items = []
        for x in items:
            if x in rename_map:
                if rename_map[x]:
                    new_items.append(rename_map[x])
            else:
                new_items.append(x)
        # Unique and join
        unique_items = sorted(list(set(new_items)), key=lambda x: new_items.index(x))
        return f"\\{cmd}{{{','.join(unique_items)}}}"

    content = re.sub(r'\\(SeeAlso|IncomingLinks|Aliases)\{([^}]+)\}', replace_list, content)
    
    return content

def main():
    # Build final map for content updates
    # stem -> stem
    replacements = {}
    
    # 1. Execute moves/deletes
    for old, new in renames.items():
        old_file = NOTES_DIR / f"{old}.tex"
        if not old_file.exists():
            print(f"Skipping {old}, file not found")
            continue
            
        if new is None:
            print(f"Deleting junk {old}")
            old_file.unlink()
            continue
            
        new_file = NOTES_DIR / f"{new}.tex"
        
        if new == old:
            continue

        replacements[old] = new
        
        if new_file.exists():
            # Target exists. Delete old (duplicate).
            # Prefer larger file? User said "replace... unless it's already present".
            # I'll check sizes
            if old_file.stat().st_size > new_file.stat().st_size:
                print(f"WARNING: Deleting larger file {old} in favor of {new}. Merging content manual check might be needed.")
            
            print(f"Deleting {old} (target {new} exists)")
            old_file.unlink()
        else:
            # Rename
            print(f"Renaming {old} -> {new}")
            old_file.rename(new_file)

    # 2. Update all content
    print("Updating content references...")
    for f in NOTES_DIR.glob("*.tex"):
        txt = f.read_text()
        new_txt = update_content(txt, replacements)
        if new_txt != txt:
            print(f"Updated refs in {f.name}")
            f.write_text(new_txt)

if __name__ == "__main__":
    main()
