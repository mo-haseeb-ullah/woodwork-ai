import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re
from pdf_extractor import clean_extracted_text

pdf_path = r"D:\ETSY\LARGE 10x12 LEAN TO SHED PLANS.pdf"
doc = pymupdf.open(pdf_path)

def parse_material_line(line):
    clean = line.lstrip("•").strip()
    if not clean:
        return None
    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean)
    if match:
        return {"quantity": match.group(1), "description": match.group(2).strip()}
    if any(kw in clean.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "hardware", "staple", "shingle", "felt"]):
        return {"quantity": "As Needed", "description": clean}
    return {"quantity": "1", "description": clean}

# 1. Parse ONLY Shopping List (from Shopping List pages 4-5)
shopping_materials = []
for p_idx in range(3, min(6, len(doc))):
    raw = doc[p_idx].get_text("text") or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l]
    # Check if page is explicitly Shopping List
    if any("shopping list" in l.lower() for l in lines[:3]):
        for l in lines:
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch"]):
                mat_item = parse_material_line(l)
                if mat_item and mat_item not in shopping_materials:
                    shopping_materials.append(mat_item)

# 2. Parse ONLY Cut List (from Step pages / Cut List pages)
cut_list_items = []
for p_idx in range(6, len(doc)):
    raw = doc[p_idx].get_text("text") or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l]
    for l in lines:
        if l.startswith("•") or (re.match(r'^\d+[\s\–\-]+', l) and ("cut" in l.lower() or "size" in l.lower() or "sheet" in l.lower() or "plywood" in l.lower() or "treated" in l.lower() or re.search(r'\d+[\′\″\']', l))):
            clean_b = l.lstrip("•").strip()
            match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_b)
            if match:
                item = {
                    "quantity": match.group(1),
                    "dimensions": match.group(2).strip(),
                    "description": "Cut Member"
                }
                if item not in cut_list_items:
                    cut_list_items.append(item)

print("=== SHOPPING LIST (Store Materials Only) ===")
for m in shopping_materials:
    print(f"Qty: {m['quantity']:4s} | Description: {m['description']}")

print("\n=== CUT LIST (Cut Dimensions Only) ===")
for c in cut_list_items:
    print(f"Qty: {c['quantity']:4s} | Dimensions: {c['dimensions']}")
