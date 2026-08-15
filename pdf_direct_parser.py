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
    if any(kw in clean.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "hardware", "staple", "shingle", "felt", "drip edge", "tack", "deck screws"]):
        return {"quantity": "As Needed", "description": clean}
    return {"quantity": "1", "description": clean}

def parse_pdf_directly(pdf_filepath):
    """
    Universal Direct PDF Parser:
    - Picture on Page 1 is ALWAYS the Cover Hero Picture (page_1_img).
    - Removes complex step logic and pastes text line-by-line page-by-page.
    - Page N picture (page_{N}_img) is strictly paired with Page N line-by-line text.
    - Differentiates Shopping List vs Cut List for overview tables.
    """
    doc = pymupdf.open(pdf_filepath)
    
    # 1. Page 1 Image is ALWAYS Hero Image
    hero_image = "page_1_img"
    
    # 2. Extract Project Title from Page 1
    page1_text = doc[0].get_text("text") or ""
    project_name = "Woodworking Plan"
    for line in page1_text.split("\n"):
        l = line.strip()
        if any(kw in l.upper() for kw in ["PLANS", "SHED", "BARN", "COOP", "TABLE", "BENCH", "DOOR", "WINDOW", "GREENHOUSE"]):
            if not any(kw in l.lower() for kw in ["legal", "disclaimer", "copyright", "construct101", "http", "page", "isbn"]):
                clean_t = re.sub(r'[\–\-]\s*(Overview|Material List|Cutting List|Shopping List).*', '', l, flags=re.I).strip()
                clean_t = re.sub(r'^ArtisanBlueprint\s*\|\s*', '', clean_t, flags=re.I).strip()
                if clean_t:
                    project_name = clean_t
                    break

    project_name = re.sub(r'[\–\-]\s*Page \d+.*', '', project_name, flags=re.I).strip()

    # 3. Overview Intro & Finished Dimensions
    intro_lines = []
    dimensions = "See Plan Drawings"
    for p_idx in range(min(3, len(doc))):
        raw = doc[p_idx].get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        for l in lines:
            if l and not any(kw in l.lower() for kw in ["legal:", "disclaimer:", "copyright", "reprinting", "prohibited", "prosecuted", "isbn-", "liability"]):
                if not any(kw in l.lower() for kw in ["overview", "material list", "shopping list", "cutting list"]):
                    intro_lines.append(l)
                    if ("x" in l.lower() or "×" in l or "'" in l or '"' in l) and (dimensions == "See Plan Drawings"):
                        if any(c.isdigit() for c in l):
                            dimensions = l
                            
    # 4. Shopping List & Cut List overview parsing
    materials = []
    cut_list = []
    current_mode = None
    
    for p_idx in range(1, min(7, len(doc))):
        raw = doc[p_idx].get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        
        for l in lines:
            l_clean = l.lower().strip()
            if re.match(r'^(shopping list|material list|materials|.*shed plans[\-\s]*material list)$', l_clean):
                current_mode = "shopping"
                continue
            elif re.match(r'^(cutting list|cut list|cut list \+ materials)$', l_clean):
                current_mode = "cutting"
                continue
            elif l_clean in ["overview", "legal:", "disclaimer:"]:
                current_mode = None
                continue
                
            if current_mode is None:
                continue
                
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["screw", "nail", "shingle", "felt", "drip edge", "roof tacks", "roofing staples"]):
                clean_l = l.lstrip("•").strip()
                if current_mode == "shopping":
                    item = parse_material_line(clean_l)
                    if item and item not in materials:
                        materials.append(item)
                elif current_mode == "cutting":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        item = {"quantity": match.group(1), "dimensions": match.group(2).strip(), "description": "Cut Member"}
                        if item not in cut_list:
                            cut_list.append(item)

    # 5. Direct Page-by-Page Paste (Pages 2 to End)
    steps = []
    step_num = 1
    
    for p_idx in range(1, len(doc)):
        page_num = p_idx + 1
        page = doc[p_idx]
        raw = page.get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        if not lines:
            continue
            
        page_text_lower = cleaned.lower()
        
        # Skip pure legal disclaimers
        if any(kw in page_text_lower for kw in ["legal:", "disclaimer:", "all rights reserved", "isbn-"]):
            lines = [l for l in lines if not any(kw in l.lower() for kw in ["legal:", "disclaimer:", "all rights reserved", "isbn-", "reprinting", "prohibited", "prosecuted"])]
            
        if not lines:
            continue

        exact_desc = "\n".join(lines)
        img_label = f"page_{page_num}_img"
        
        steps.append({
            "step_number": step_num,
            "title": f"STEP {step_num}",
            "page_number": page_num,
            "exact_description": exact_desc,
            "image_sources": [img_label]
        })
        step_num += 1

    return {
        "project_name": project_name,
        "project_intro": " ".join(intro_lines[:5]) if intro_lines else f"Complete DIY construction guide for {project_name}.",
        "difficulty_level": "Intermediate DIY",
        "finished_dimensions": dimensions,
        "hero_image_source": hero_image, # Page 1 Image is ALWAYS Hero Image
        "dimension_image_source": "page_2_img",
        "tools_image_source": None,
        "materials": materials,
        "cut_list": cut_list,
        "tools": [{"name": "Miter Saw"}, {"name": "Circular Saw"}, {"name": "Framing Hammer"}, {"name": "Tape Measure"}, {"name": "Level"}],
        "steps": steps,
        "finishing_instructions": ["Apply primer and two coats of exterior grade paint or stain.", "Caulk all exterior joints with paintable silicone."],
        "missing_images": []
    }
