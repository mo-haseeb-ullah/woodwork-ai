import os
import re
import pymupdf
from pdf_extractor import clean_extracted_text

def parse_material_line(line):
    clean = line.lstrip("•").strip()
    if not clean:
        return None
    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean)
    if match:
        return {"quantity": match.group(1), "description": match.group(2).strip()}
    if any(kw in clean.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "hardware", "staple", "shingle", "felt", "drip edge"]):
        return {"quantity": "As Needed", "description": clean}
    return {"quantity": "1", "description": clean}

def is_shopping_line(line):
    l = line.lower()
    if any(kw in l for kw in ["nail", "screw", "shingle", "felt", "tack", "staple", "edge", "flashing", "hinge", "latch", "hardware"]):
        return True
    if re.search(r'[\–\-]\s*(8′|10′|12′|14′|16′|8\'|10\'|12\'|14\'|16\')\s*$', line) and not re.search(r'\d+\s*(″|in|inch|1/2|1/4|3/4|3/8|5/8|7/8|7/16)', line):
        return True
    return False

def is_cut_line(line):
    l = line.lower()
    if any(kw in l for kw in ["cut to size", "cut member"]):
        return True
    if re.search(r'\d+\s*(″|in|inch|1/2|1/4|3/4|3/8|5/8|7/8|7/16)', line):
        return True
    if re.search(r'[\–\-]\s*\d+[\′\']\s*\d+', line):
        return True
    return False

def parse_pdf_directly(pdf_filepath):
    """
    Universal Python PDF parser that strictly differentiates between:
    - SHOPPING LIST: Store purchase list (stock lumber 8', 10', 12', nails, screws, shingles, drip edge)
    - CUTTING LIST: Exact cut pieces with specific measured dimensions (3' 9", 3' 8 1/4", 4'x4')
    And formats step headings to write ONLY the step number (STEP 1, STEP 2, etc.).
    """
    doc = pymupdf.open(pdf_filepath)
    
    project_name = "Woodworking Plan"
    project_intro = ""
    dimensions = "See Plan Drawings"
    materials = []
    cut_list = []
    steps = []
    
    # 1. Parse Project Title (Pages 1-2)
    for page_idx in range(min(2, len(doc))):
        raw = doc[page_idx].get_text("text") or ""
        lines = [
            l.strip() for l in raw.split("\n") 
            if l.strip() and "Construct101" not in l and "Legal:" not in l and "Disclaimer:" not in l 
            and not re.search(r'ArtisanBlueprint|Page \d+', l, re.I)
        ]
        for line in lines:
            clean_line = re.sub(r'[\–\-]\s*(Overview|Material List|Cutting List|Shopping List).*', '', line, flags=re.I).strip()
            clean_line = re.sub(r'^ArtisanBlueprint\s*\|\s*', '', clean_line, flags=re.I).strip()
            if any(kw in clean_line.upper() for kw in ["PLANS", "SHED", "WOOD", "BUILD", "TABLE", "BENCH", "DESK", "CABINET", "DOOR", "WINDOW", "COOP", "CHICKEN"]):
                project_name = clean_line
                break
        if project_name != "Woodworking Plan":
            break

    project_name = re.sub(r'[\–\-]\s*Page \d+.*', '', project_name, flags=re.I).strip()

    # 2. Parse Overview & Dimensions (Pages 1-3)
    intro_lines = []
    for page_idx in range(min(3, len(doc))):
        raw = doc[page_idx].get_text("text") or ""
        lines = [
            l.strip() for l in raw.split("\n") 
            if l.strip() and "Construct101" not in l and not re.search(r'ArtisanBlueprint|Page \d+', l, re.I)
        ]
        for l in lines:
            if l.lower() not in ["overview", "1", "2", "3"] and not l.startswith("http"):
                if not any(kw in l.lower() for kw in ["legal:", "material list", "shopping list", "cutting list"]):
                    intro_lines.append(l)
                    if ("x" in l.lower() or "×" in l or "'" in l or '"' in l) and (not dimensions or dimensions == "See Plan Drawings"):
                        if any(c.isdigit() for c in l):
                            dimensions = l
                        
    if intro_lines:
        project_intro = clean_extracted_text(" ".join(intro_lines[:8]))

    # 3. Parse Material List & Cutting List (Pages 3 to 6)
    for page_idx in range(2, min(6, len(doc))):
        raw = doc[page_idx].get_text("text") or ""
        lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and not re.search(r'Page \d+', l, re.I)]
        for l in lines:
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["nail", "screw", "shingle", "felt", "drip edge", "flashing"]):
                clean_l = l.lstrip("•").strip()
                if is_shopping_line(clean_l):
                    item = parse_material_line(clean_l)
                    if item and item not in materials:
                        materials.append(item)
                elif is_cut_line(clean_l):
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        item = {
                            "quantity": match.group(1),
                            "dimensions": match.group(2).strip(),
                            "description": "Cut Member"
                        }
                        if item not in cut_list:
                            cut_list.append(item)

    # 4. Dynamic Step Processing (Pages 4 to End)
    start_step_page = 3
    step_num = 1
    
    for page_idx in range(start_step_page, len(doc)):
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
            
        if any(l.lower().endswith("overview") or "material list" in l.lower() or "shopping list" in l.lower() or "cutting list" in l.lower() for l in clean_lines[:2]):
            continue

        step_bullets = []
        instruction_lines = []
        
        for l in clean_lines:
            if l.startswith("STEP "):
                continue
            if l.startswith("•") or (re.match(r'^\d+[\s\–\-]+', l) and ("cut" in l.lower() or "size" in l.lower() or "sheet" in l.lower() or "plywood" in l.lower() or "treated" in l.lower() or re.search(r'\d+[\′\″\']', l))):
                clean_b = l.lstrip("•").strip()
                if clean_b and clean_b not in step_bullets:
                    step_bullets.append(clean_b)
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_b)
                    if match:
                        c_item = {
                            "quantity": match.group(1),
                            "dimensions": match.group(2).strip(),
                            "description": f"Step {step_num} Member"
                        }
                        if c_item not in cut_list:
                            cut_list.append(c_item)
            else:
                instruction_lines.append(l)
                
        step_desc = clean_extracted_text(" ".join(instruction_lines))
        if not step_desc:
            step_desc = clean_extracted_text(" ".join(clean_lines))
            
        page_num = page_idx + 1
        img_label = f"page_{page_num}_img"
        
        steps.append({
            "step_number": step_num,
            "title": f"STEP {step_num}",
            "step_materials": step_bullets,
            "exact_description": step_desc,
            "image_sources": [img_label]
        })
        step_num += 1

    return {
        "project_name": project_name,
        "project_intro": project_intro if project_intro else f"Complete DIY construction guide for {project_name}.",
        "difficulty_level": "Intermediate DIY",
        "finished_dimensions": dimensions,
        "hero_image_source": "page_1_img",
        "dimension_image_source": "page_2_img",
        "tools_image_source": "page_3_img",
        "materials": materials,
        "cut_list": cut_list,
        "tools": [{"name": "Miter Saw"}, {"name": "Circular Saw"}, {"name": "Framing Hammer"}, {"name": "Tape Measure"}, {"name": "Level"}],
        "steps": steps,
        "finishing_instructions": ["Apply primer and two coats of exterior grade paint or stain.", "Caulk all exterior joints with paintable silicone."],
        "missing_images": []
    }
