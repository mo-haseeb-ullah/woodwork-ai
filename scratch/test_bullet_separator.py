import sys
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re

pdf_path = r"C:\Users\My PC\Downloads\Large-10x12-Lean-To-Shed-Plans.pdf"
doc = pymupdf.open(pdf_path)

print("=== STEP BULLET & PARAGRAPH SEPARATION TEST ===")
for page_idx in range(6, len(doc)):
    page_num = page_idx + 1
    step_num = page_idx - 5
    raw = doc[page_idx].get_text("text") or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l and "Legal:" not in l and "Disclaimer:" not in l]
    
    clean_lines = [l for l in lines if l not in ["•", "″", "′", "-"]]
    
    if not clean_lines:
        continue
        
    title = clean_lines[0]
    bullets = []
    instruction_lines = []
    
    for l in clean_lines[1:]:
        if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or "cut to size" in l.lower() or "sheet" in l.lower() or ("plywood" in l.lower() and not l.startswith("Measure")):
            clean_b = l.lstrip("•").strip()
            if clean_b:
                bullets.append(clean_b)
        else:
            instruction_lines.append(l)
            
    instructions = " ".join(instruction_lines).strip()
    
    print(f"\n--- STEP {step_num}: {title} (Page {page_num}) ---")
    print("BULLETS:", bullets)
    print("INSTRUCTIONS:", instructions[:100] + "..." if len(instructions) > 100 else instructions)
