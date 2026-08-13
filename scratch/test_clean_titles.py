import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re
from pdf_extractor import clean_extracted_text

pdf_path = r"D:\ETSY\LARGE 10x12 LEAN TO SHED PLANS.pdf"
doc = pymupdf.open(pdf_path)

known_headings = [
    "floor", "front wall", "back wall", "right/left wall", "roof", 
    "wire mesh", "trim", "door", "roof deck", "rafters", "siding",
    "shed window framing", "shed single door", "shed double door",
    "front/back wall frame", "right/left wall frame", "front top wall frame",
    "door and window framing", "front/back wall frame ends", "raise and secure wall frames",
    "rafter cut details", "rafter installation", "top wall studs & overhang blocking",
    "siding installation", "roof purlins", "purlin blocking", "metal corrugated roofing panels",
    "door installation", "corner & window trim"
]

step_num = 1

for page_idx in range(6, len(doc)):
    page = doc[page_idx]
    raw = page.get_text("text") or ""
    raw_lines = [l.strip() for l in raw.split("\n") if l.strip()]
    
    clean_lines = []
    for l in raw_lines:
        if "Construct101" in l or "Legal:" in l or "Disclaimer:" in l:
            continue
        if re.search(r'ArtisanBlueprint.*Page \d+|Page \d+$', l, re.I):
            continue
        if l in ["•", "″", "′", "-"] or l.isdigit() or l.startswith("Visit www"):
            continue
        clean_lines.append(l)
        
    if not clean_lines:
        continue
        
    first_line = clean_lines[0]
    
    # Extract explicit STEP X: Title if present
    step_match = re.match(r'^STEP\s*\d+\s*:\s*(.+)', first_line, re.I)
    if step_match:
        step_title = step_match.group(1).strip()
        content_lines = clean_lines[1:]
    else:
        # Check if first line is a clean section heading
        clean_header = first_line.rstrip(":")
        if any(h in clean_header.lower() for h in known_headings) and len(clean_header) < 40 and not any(kw in clean_header.lower() for kw in ["cut ", "install ", "measure ", "build ", "raise "]):
            step_title = clean_header
            content_lines = clean_lines[1:]
        else:
            # Fallback title -> ALL text goes into description!
            step_title = f"Step {step_num}"
            content_lines = clean_lines
            
    # Clean up step_title: remove any long instruction sentences if present
    if len(step_title) > 40 or any(kw in step_title.lower() for kw in ["cut ", "install ", "measure ", "build ", "raise ", "nail "]):
        step_title = f"Step {step_num}"
        content_lines = clean_lines
        
    step_desc = clean_extracted_text(" ".join(content_lines))
    
    print(f"STEP {step_num}: Title = '{step_title}'")
    print(f"         Description = '{step_desc}'\n")
    step_num += 1
