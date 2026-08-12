import pymupdf
import re
import json

pdf_path = r"C:\Users\My PC\Downloads\Large-10x12-Lean-To-Shed-Plans.pdf"
doc = pymupdf.open(pdf_path)

def parse_material_line(line):
    clean = line.lstrip("•").strip()
    if not clean:
        return None
    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean)
    if match:
        return {"quantity": match.group(1), "description": match.group(2).strip()}
    # Fallback for hardware/nails without leading numbers
    if any(kw in clean.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "hardware"]):
        return {"quantity": "As Needed", "description": clean}
    return None

shopping_materials = []
for p_idx in range(3, 5):
    raw = doc[p_idx].get_text("text") or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l]
    for l in lines:
        if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l):
            item = parse_material_line(l)
            if item and item not in shopping_materials:
                shopping_materials.append(item)

# Build Structured Cut List from Step Pages
cut_list_items = [
    {"quantity": "2", "dimensions": "2×6 – 12′", "description": "Pressure Treated Floor Runners"},
    {"quantity": "10", "dimensions": "2×6 – 9′ 9″", "description": "Floor Joists"},
    {"quantity": "3", "dimensions": "4×4 – 12′", "description": "Pressure Treated Floor Skids"},
    {"quantity": "4", "dimensions": "3/4″ (4′x8′ Sheet)", "description": "Tongue and Groove Floor Deck Plywood"},
    {"quantity": "4", "dimensions": "2×4 – 12′", "description": "Front & Back Wall Plates"},
    {"quantity": "28", "dimensions": "2×4 – 7′ 6″", "description": "Front & Back Wall Studs"},
    {"quantity": "2", "dimensions": "2×4 – 11′ 5″", "description": "Front Wall Headers"},
    {"quantity": "4", "dimensions": "2×4 – 9′ 5″", "description": "Side Wall Plates"},
    {"quantity": "18", "dimensions": "2×4 – 7′ 6″", "description": "Side Wall Studs"},
    {"quantity": "2", "dimensions": "2×4 – 10′", "description": "Side Wall Top Plates"},
    {"quantity": "1", "dimensions": "2×4 – 12′", "description": "Front Top Wall Plate"},
    {"quantity": "10", "dimensions": "2×4 – 18 1/2″", "description": "Front Top Wall Studs"},
    {"quantity": "10", "dimensions": "2×4 – 11′ 10 3/8″", "description": "Rafters"},
    {"quantity": "6", "dimensions": "2×4 – 8′", "description": "Side Top Wall Studs"},
    {"quantity": "13", "dimensions": "4′x8′ Sheet", "description": "T1-11 Exterior Siding"},
    {"quantity": "7", "dimensions": "2×4 – 14′", "description": "Roof Purlins"},
    {"quantity": "3", "dimensions": "2×4 – 8′", "description": "Purlin Blocking"},
    {"quantity": "10", "dimensions": "1×4 – 10′", "description": "Corner & Window Trim"}
]

print("=== SHOPPING LIST ITEMS ===")
print(json.dumps(shopping_materials, indent=2))

print("\n=== CUT LIST ITEMS ===")
print(json.dumps(cut_list_items, indent=2))
