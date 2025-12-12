#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from multiprocessing import Pool

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO_ROOT / "notes"
PDFS_DIR = REPO_ROOT / "pdfs"
HTML_DIR = REPO_ROOT / "html"
BUILD_DIR = REPO_ROOT / "build"

def needs_rebuild(source, target):
    if not target.exists():
        return True
    return source.stat().st_mtime > target.stat().st_mtime

def build_pdf(note_path):
    note_name = note_path.stem
    pdf_path = PDFS_DIR / f"{note_name}.pdf"
    
    if needs_rebuild(note_path, pdf_path):
        print(f"Building PDF: {note_name}")
        # Call existing script
        cmd = ["bash", "scripts/build-note.sh", str(note_path), str(BUILD_DIR)]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0:
            # Move result
            built_pdf = BUILD_DIR / f"{note_name}.pdf"
            if built_pdf.exists():
                os.rename(built_pdf, pdf_path)
            return True
        else:
            print(f"Error building {note_name}:\n{res.stderr.decode()}")
            return False
    return False

def build_html(note_path):
    note_name = note_path.stem
    # Skip meta files
    if "demo" in note_name or "debug" in note_name:
        return False
        
    html_path = HTML_DIR / f"{note_name}.html"
    
    # tex-to-html.py handles its own output path usually, but let's be explicit
    # Check modification of tex vs html
    # AND check modification of the script itself!
    script_mtime = Path("scripts/tex-to-html.py").stat().st_mtime
    
    rebuild = False
    if not html_path.exists():
        rebuild = True
    elif note_path.stat().st_mtime > html_path.stat().st_mtime:
        rebuild = True
    elif script_mtime > html_path.stat().st_mtime:
        rebuild = True
        
    if rebuild:
        print(f"Building HTML: {note_name}")
        cmd = ["python3", "scripts/tex-to-html.py", str(note_path), str(html_path)]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            print(f"Error building HTML {note_name}:\n{res.stderr.decode()}")
            return False
        return True
    return False

def build_all(target="all"):
    NOTES_DIR.mkdir(exist_ok=True)
    PDFS_DIR.mkdir(exist_ok=True)
    HTML_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)

    notes = list(NOTES_DIR.glob("*.tex"))
    
    if target == "clean":
        import shutil
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(PDFS_DIR, ignore_errors=True)
        shutil.rmtree(HTML_DIR, ignore_errors=True)
        print("Cleaned.")
        return

    # Parallel build
    pool = Pool()
    
    if target in ["all", "web", "pdf"]:
        pool.map(build_pdf, notes)
        
    if target in ["web", "html"]:
        # Ensure CSS is present
        style_src = REPO_ROOT / "lib" / "style.css"
        style_dst = HTML_DIR / "style.css"
        if style_src.exists():
            import shutil
            shutil.copy(style_src, style_dst)
            
        pool.map(build_html, notes)
        
    pool.close()
    pool.join()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    build_all(target)
