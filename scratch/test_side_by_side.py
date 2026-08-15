import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re

pdf_path = r"D:\ETSY\LARGE 10x12 LEAN TO SHED PLANS.pdf"
doc = pymupdf.open(pdf_path)

def is_shopping_item(line):
    # Standard stock lumber (8', 10', 12', 16') or Hardware/Fasteners
    l = line.lower()
    if any(kw in l for kw in ["nail", "screw", "shingle", "felt", "tack", "staple", "edge", "flashing", "hinge", "latch", "glue", "primer", "paint"]):
        return True
    # Stock lengths (8', 10', 12', 14', 16') without specific cut fractions
    if re.search(r'[\–\-]\s*(8′|10′|12′|14′|16′|8\'|10\'|12\'|14\'|16\')\s*$', line) and not re.search(r'\d+\s*(″|in|inch|1/2|1/4|3/4|3/8|5/8|7/8|7/16)', line):
        return True
    return False

def is_cut_item(line):
    # Cut dimensions containing specific lengths, fractions, or cut to size
    l = line.lower()
    if any(kw in l for kw in ["cut to size", "cut member"]):
        return True
    if re.search(r'\d+\s*(″|in|inch|1/2|1/4|3/4|3/8|5/8|7/8|7/16|9\s*9|5\s*10|2\s*11)', line):
        return True
    if re.search(r'[\–\-]\s*\d+[\′\']\s*\d+', line):
        return True
    return False

shopping_list = []
cutting_list = []

for page in doc:
    raw = page.get_text("text") or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l]
    for l in lines:
        if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["nail", "screw", "shingle", "felt", "drip edge", "flashing"]):
            clean_l = l.lstrip("•").strip()
            if is_shopping_item(clean_l):
                if clean_l not in shopping_list:
                    shopping_list.append(clean_l)
            elif is_cut_item(clean_l):
                if clean_l not in cutting_list:
                    cutting_list.append(clean_l)

print("=== SHOPPING LIST (Stock Lumber & Store Hardware) ===")
for item in shopping_list:
    print(" -", item)

print("\n=== CUTTING LIST (Exact Cut Dimensions & Part Sizes) ===")
for item in cutting_list:
    print(" -", item)
