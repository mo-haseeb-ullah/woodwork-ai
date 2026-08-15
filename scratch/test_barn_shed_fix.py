import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re

pdf_path = r"D:\Plans\10x10-Barn-Shed-Plans.pdf"
doc = pymupdf.open(pdf_path)

def parse_barn_shed_header_fixed(doc):
    materials = []
    cut_list = []
    
    current_mode = None # "shopping" or "cutting"
    
    for page_idx in range(len(doc)):
        raw = doc[page_idx].get_text("text") or ""
        lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and not re.search(r'Page \d+', l, re.I)]
        
        # Check if page is step page (Page 8+)
        if page_idx >= 7 and any(l.startswith("Floor") or l.startswith("Walls") or l.startswith("Truss") or l.startswith("Roof") or l.startswith("Siding") for l in lines[:3]):
            current_mode = None
            
        for l in lines:
            l_clean = l.lower().strip()
            
            # Switch modes ONLY on strict section header lines (not sentences containing the phrase)
            if re.match(r'^(shopping list|material list|materials|shopping list \(materials to buy\)|10×10 barn shed plans[\-\s]*material list)$', l_clean):
                current_mode = "shopping"
                continue
            elif re.match(r'^(cutting list|cut list|cut list \+ materials)$', l_clean):
                current_mode = "cutting"
                continue
                
            if current_mode is None:
                continue
                
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["screw", "nail", "shingle", "felt", "drip edge", "roof tacks", "roofing staples"]):
                clean_l = l.lstrip("•").strip()
                
                if current_mode == "shopping":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        item = {"quantity": match.group(1), "description": match.group(2).strip()}
                    else:
                        item = {"quantity": "As Needed", "description": clean_l}
                    if item not in materials:
                        materials.append(item)
                        
                elif current_mode == "cutting":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        item = {
                            "quantity": match.group(1),
                            "dimensions": match.group(2).strip(),
                            "description": "Cut Member"
                        }
                        if item not in cut_list:
                            cut_list.append(item)

    return materials, cut_list

mats, cuts = parse_barn_shed_header_fixed(doc)

print(f"=== PERFECT SHOPPING LIST ({len(mats)} items) ===")
for m in mats:
    print(f"  Qty: {m['quantity']:9s} | {m['description']}")

print(f"\n=== PERFECT CUTTING LIST ({len(cuts)} items) ===")
for c in cuts:
    print(f"  Qty: {c['quantity']:4s} | Dim: {c['dimensions']:40s} | Part: {c['description']}")
