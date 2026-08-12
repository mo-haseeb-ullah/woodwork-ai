import sys
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re

pdf_path = r"C:\Users\My PC\Downloads\Large-10x12-Lean-To-Shed-Plans.pdf"
doc = pymupdf.open(pdf_path)

KNOWN_TITLES = {
    7: "Floor Frame",
    8: "Floor Deck",
    9: "Front/Back Wall Frame",
    10: "Door and Window Framing",
    11: "Front/Back Wall Frame Ends",
    12: "Right/Left Wall Frame",
    13: "Raise and Secure Wall Frames",
    14: "Front Top Wall Frame",
    15: "Rafter Cut Details",
    16: "Rafter Installation",
    17: "Top Wall Studs & Overhang Blocking",
    18: "Siding Installation",
    19: "Roof Purlins",
    20: "Purlin Blocking",
    21: "Metal Corrugated Roofing Panels",
    22: "Door Installation",
    23: "Corner & Window Trim"
}

print("=== EXACT TEXT PRESERVATION TEST ===")
for page_idx in range(6, len(doc)):
    page_num = page_idx + 1
    step_num = page_idx - 5
    raw = doc[page_idx].get_text("text") or ""
    
    # Filter out website headers/footers
    lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l and "Legal:" not in l and "Disclaimer:" not in l]
    
    # Clean standalone units/symbols
    clean_lines = [l for l in lines if l not in ["•", "″", "′", "-"]]
    
    title = KNOWN_TITLES.get(page_num, f"Step {step_num}")
    bullets = []
    instruction_lines = []
    
    for l in clean_lines:
        if l in ["Floor", "Walls", "Rafters", "Siding", "Roof", "Door", "Trim", "Front/Back Wall Frame:", "Right/Left Wall Frame:", "Front Top Wall Frame:"]:
            continue
        if re.match(r'^\d+[\s\–\-]+', l) or "cut to size" in l.lower() or "sheet" in l.lower() or ("plywood" in l.lower() and not l.startswith("Measure")):
            bullets.append(l.lstrip("•").strip())
        else:
            instruction_lines.append(l)
            
    instructions = " ".join(instruction_lines).strip()
    
    print(f"\n--- STEP {step_num}: {title} (Page {page_num}) ---")
    print("BULLETS:", bullets)
    print("TEXT:", instructions)
