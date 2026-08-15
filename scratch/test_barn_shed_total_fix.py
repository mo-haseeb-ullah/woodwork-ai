import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re
from pdf_extractor import clean_extracted_text

pdf_path = r"D:\ETSY\10x10 Barn Shed Plans.pdf"
doc = pymupdf.open(pdf_path)

def parse_barn_shed_perfectly(doc):
    project_name = "Woodworking Plan"
    project_intro = ""
    dimensions = "See Plan Drawings"
    materials = []
    cut_list = []
    steps = []
    
    # 1. Project Title (Page 1 - 2)
    for p_idx in range(min(2, len(doc))):
        raw = doc[p_idx].get_text("text") or ""
        for line in raw.split("\n"):
            l = line.strip()
            if any(kw in l.upper() for kw in ["PLANS", "SHED", "BARN", "COOP", "TABLE", "BENCH", "DOOR", "WINDOW"]):
                if not any(kw in l.lower() for kw in ["legal", "disclaimer", "copyright", "construct101", "http", "page"]):
                    project_name = re.sub(r'[\–\-]\s*(Overview|Material List|Cutting List|Shopping List).*', '', l, flags=re.I).strip()
                    break
        if project_name != "Woodworking Plan":
            break

    # 2. Project Intro & Dimensions (Ignore Legal text)
    intro_lines = []
    for p_idx in range(min(3, len(doc))):
        raw = doc[p_idx].get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        for line in cleaned.split("\n"):
            l = line.strip()
            if l and not any(kw in l.lower() for kw in ["legal:", "disclaimer:", "copyright", "reprinting", "prohibited", "prosecuted", "isbn-", "liability"]):
                if not any(kw in l.lower() for kw in ["overview", "material list", "shopping list", "cutting list"]):
                    intro_lines.append(l)
                    if ("x" in l.lower() or "×" in l or "'" in l or '"' in l) and (dimensions == "See Plan Drawings"):
                        if any(c.isdigit() for c in l):
                            dimensions = l
                            
    if intro_lines:
        project_intro = " ".join(intro_lines[:5])
        
    # 3. Materials & Cut List (Pages 5, 6, 7)
    current_mode = None
    for p_idx in range(1, min(7, len(doc))):
        raw = doc[p_idx].get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        
        for l in lines:
            l_clean = l.lower().strip()
            if re.match(r'^(shopping list|material list|materials|.*barn shed plans[\-\s]*material list)$', l_clean):
                current_mode = "shopping"
                continue
            elif re.match(r'^(cutting list|cut list|cut list \+ materials)$', l_clean):
                current_mode = "cutting"
                continue
                
            if current_mode is None:
                continue
                
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l_clean for kw in ["screw", "nail", "shingle", "felt", "drip edge", "roof tacks", "roofing staples"]):
                clean_l = l.lstrip("•").strip()
                if current_mode == "shopping":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    item = {"quantity": match.group(1), "description": match.group(2).strip()} if match else {"quantity": "As Needed", "description": clean_l}
                    if item not in materials:
                        materials.append(item)
                elif current_mode == "cutting":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        item = {"quantity": match.group(1), "dimensions": match.group(2).strip(), "description": "Cut Member"}
                        if item not in cut_list:
                            cut_list.append(item)

    # 4. Construction Steps (Starts strictly on Page 8 - Floor Framing)
    step_num = 1
    for p_idx in range(7, len(doc)): # Page 8 onwards (0-indexed 7)
        page_num = p_idx + 1
        raw = doc[p_idx].get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        if not lines:
            continue
            
        exact_desc = " ".join(lines)
        exact_desc = clean_extracted_text(exact_desc)
        
        steps.append({
            "step_number": step_num,
            "title": f"STEP {step_num}",
            "page_number": page_num,
            "exact_description": exact_desc,
            "image_sources": [f"page_{page_num}_img"]
        })
        step_num += 1

    return {
        "project_name": project_name,
        "project_intro": project_intro if project_intro else f"Complete DIY construction guide for {project_name}.",
        "finished_dimensions": dimensions,
        "hero_image_source": "page_2_img", # 3D Rendering of Shed on Page 2
        "dimension_image_source": "page_3_img", # Dimensions diagram on Page 3
        "materials": materials,
        "cut_list": cut_list,
        "steps": steps
    }

res = parse_barn_shed_perfectly(doc)

print("=== PROJECT TITLE ===")
print("Title:", res["project_name"])

print("\n=== PROJECT INTRO ===")
print("Intro:", res["project_intro"])

print("\n=== FINISHED DIMENSIONS ===")
print("Dimensions:", res["finished_dimensions"])

print("\n=== HERO & DIMENSION IMAGES ===")
print("Hero Image:", res["hero_image_source"])
print("Dimension Image:", res["dimension_image_source"])

print(f"\n=== TABLES ===")
print(f"Shopping List: {len(res['materials'])} items")
print(f"Cut List: {len(res['cut_list'])} items")

print(f"\n=== STEP 1 (Source Page {res['steps'][0]['page_number']}) ===")
print("Title:", res['steps'][0]['title'])
print("Image:", res['steps'][0]['image_sources'])
print("Description:", res['steps'][0]['exact_description'])

print(f"\n=== STEP 2 (Source Page {res['steps'][1]['page_number']}) ===")
print("Title:", res['steps'][1]['title'])
print("Image:", res['steps'][1]['image_sources'])
print("Description:", res['steps'][1]['exact_description'])
