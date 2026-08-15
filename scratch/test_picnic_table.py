import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re

def parse_pdf_materials_advanced(doc):
    shopping_materials = []
    cut_list_items = []
    
    current_mode = None  # "shopping" or "cutting"
    current_category = "" # "TABLE", "BENCH", etc.
    
    for page_idx in range(len(doc)):
        raw = doc[page_idx].get_text("text") or ""
        lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and not re.search(r'Page \d+', l, re.I)]
        
        for l in lines:
            l_lower = l.lower()
            
            # Detect Section Headers
            if "shopping list" in l_lower:
                current_mode = "shopping"
                continue
            elif "cutting list" in l_lower or "cut list" in l_lower:
                current_mode = "cutting"
                continue
            elif "overview" in l_lower:
                current_mode = None
                continue
                
            # Detect Sub-Categories (e.g. TABLE, BENCH, FRAME)
            if l.isupper() and len(l) < 25 and not re.match(r'^\d+', l) and l not in ["SHOPPING LIST", "CUTTING LIST", "MATERIAL LIST"]:
                current_category = l
                continue
                
            # If line starts with part label like (A), (B), (C), (D) or quantity number
            part_letter = None
            letter_match = re.match(r'^\(([A-Z])\)\s*(.+)', l)
            if letter_match:
                part_letter = f"Part {letter_match.group(1)}"
                l = letter_match.group(2).strip()
                
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["nail", "screw", "shingle", "felt", "staple", "deck screws"]):
                clean_l = l.lstrip("•").strip()
                
                if current_mode == "shopping":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        qty = match.group(1)
                        desc = match.group(2).strip()
                        if current_category:
                            desc = f"{current_category}: {desc}"
                        item = {"quantity": qty, "description": desc}
                        if item not in shopping_materials:
                            shopping_materials.append(item)
                    else:
                        desc = clean_l
                        if current_category:
                            desc = f"{current_category}: {desc}"
                        item = {"quantity": "As Needed", "description": desc}
                        if item not in shopping_materials:
                            shopping_materials.append(item)
                            
                elif current_mode == "cutting":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        qty = match.group(1)
                        dims = match.group(2).strip()
                        part_desc = part_letter if part_letter else (f"{current_category} Member" if current_category else "Cut Member")
                        item = {"quantity": qty, "dimensions": dims, "description": part_desc}
                        if item not in cut_list_items:
                            cut_list_items.append(item)

    return shopping_materials, cut_list_items

# Test on PDF
pdf_path = r"D:\ETSY\LARGE 10x12 LEAN TO SHED PLANS.pdf"
doc = pymupdf.open(pdf_path)
shop, cut = parse_pdf_materials_advanced(doc)

print("=== ADVANCED SHOPPING LIST ===")
for s in shop:
    print(f"Qty: {s['quantity']:9s} | {s['description']}")

print("\n=== ADVANCED CUTTING LIST ===")
for c in cut:
    print(f"Qty: {c['quantity']:4s} | Dim: {c['dimensions']:30s} | Part: {c['description']}")
