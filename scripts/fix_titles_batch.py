import os
import re
from pathlib import Path

def title_case(s):
    # Custom title case that respects things like (∞,1)
    # Simple strategy: split by space/hyphen, capitalize if not connector
    parts = re.split(r'([ -])', s)
    res = []
    for p in parts:
        if p in ['-', ' ']:
            res.append(p)
        elif not p:
            continue
        else:
            # Check if it starts with ( or math
            if p.startswith('('):
                res.append(p)
            elif p.lower() in ['of', 'in', 'an', 'a', 'the', 'and', 'for', 'to', 'at', 'by']:
                res.append(p.lower())
            else:
                res.append(p.capitalize())
    return "".join(res)

fixes = {
    "jacobi-identity": "Jacobi Identity",
    "partition-of-unity": "Partition of Unity",
    "positive-definite-form": "Positive Definite Form",
    "smooth-manifold": "Smooth Manifold",
    "hopf-algebra": "Hopf Algebra",
    "bounded-spread-haag-duality": "Bounded Spread Haag Duality",
    "tensor-field": "Tensor Field",
    "linear connection 1-form": "Linear Connection 1-Form",
    "presemisimple 2-category": "Presemisimple 2-Category",
    "equivalence in an (∞,n)-category": "Equivalence in an (∞,n)-Category",
    "n-condensation in an n-category": "n-Condensation in an n-Category",
    "2-condensation in a 2-category": "2-Condensation in a 2-Category",
    "terminal object in an (∞,1)-category": "Terminal Object in an (∞,1)-Category",
    "(∞,1)-pullback in an (∞,1)-category": "(∞,1)-Pullback in an (∞,1)-Category",
    "components in presemisimple linear 2-categories": "Components in Presemisimple Linear 2-Categories",
    "H*-bimodule": "H*-Bimodule",
    "(pseudo-)Riemannian metric": "(Pseudo-)Riemannian Metric",
    "3-manifold": "3-Manifold",
    "DG-category": "DG-Category",
    "DG-algebra": "DG-Algebra",
    "DG-module": "DG-Module",
    "Cauchy complete n-category": "Cauchy Complete n-Category",
    "cohomology": "Cohomology",
    "signature of a manifold": "Signature of a Manifold",
    "monoid in a monoidal category": "Monoid in a Monoidal Category",
    "pointed object": "Pointed Object",
    "extended isotopy": "Extended Isotopy",
    "natural transformation": "Natural Transformation",
    "premodular fusion category": "Premodular Fusion Category",
    "Levin–Wen Theory": "Levin–Wen Theory", # Already good
    "Eilenberg–MacLane space": "Eilenberg–MacLane Space",
    "seiberg–witten-theory": "Seiberg–Witten Theory",
}

notes_dir = Path("notes")
for f in notes_dir.glob("*.tex"):
    txt = f.read_text()
    match = re.search(r'\\Title\{([^}]+)\}', txt)
    if match:
        old_title = match.group(1)
        new_title = old_title
        
        # Apply specific fixes
        if old_title in fixes:
            new_title = fixes[old_title]
        elif "-" in old_title and " " not in old_title and len(old_title) > 10:
             # Heuristic for slugs that I missed
             # e.g. some-slug
             new_title = title_case(old_title.replace("-", " "))
        
        if new_title != old_title:
            print(f"Fixing {f.name}: {old_title} -> {new_title}")
            txt = txt.replace(f"\\Title{{{old_title}}}", f"\\Title{{{new_title}}}")
            f.write_text(txt)

