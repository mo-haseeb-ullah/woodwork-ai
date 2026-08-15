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
    Universal Python PDF parser with strict 1-to-1 page-to-page alignment:
    - Page N text is strictly matched with Page N diagram image (page_{N}_img).
    - Removes 'Visit www.Construct101.com for more DIY Projects Page N' and 'www.Construct101.com' from every page.
    - Differentiates Shopping List (store purchase items) vs Cut List (cut members) with zero cross-contamination.
    - Step titles write ONLY STEP 1, STEP 2, STEP 3 ... STEP N with zero extra text.
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
        raw_clean = clean_extracted_text(raw)
        lines = [l.strip() for l in raw_clean.split("\n") if l.strip()]
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
        cleaned = clean_extracted_text(raw)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        for l in lines:
            if l.lower() not in ["overview", "1", "2", "3"] and not l.startswith("http"):
                if not any(kw in l.lower() for kw in ["legal:", "disclaimer:", "material list", "shopping list", "cutting list"]):
                    intro_lines.append(l)
                    if ("x" in l.lower() or "×" in l or "'" in l or '"' in l) and (not dimensions or dimensions == "See Plan Drawings"):
                        if any(c.isdigit() for c in l):
                            dimensions = l
                        
    if intro_lines:
        project_intro = clean_extracted_text(" ".join(intro_lines[:8]))

    # 3. Parse Material List & Cutting List (Pages 1 to 7)
    current_mode = None  # "shopping" or "cutting"
    current_category = ""  # "TABLE", "BENCH", "FRAME"
    
    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        raw = doc[page_idx].get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        
        # Stop material/cutting list extraction when actual construction steps begin
        page_text_lower = cleaned.lower()
        is_step_page = any(kw in page_text_lower for kw in ["step 1", "step 2", "cut two", "cut nine", "cut four", "cut 2x4", "cut 2x6", "joist are spaced", "wall studs are spaced"])
        if is_step_page and page_num >= 4:
            current_mode = None
            
        for l in lines:
            l_clean = l.lower().strip()
            
            # Switch modes ONLY on strict section header lines
            if re.match(r'^(shopping list|material list|materials|shopping list \(materials to buy\)|.*shed plans[\-\s]*material list)$', l_clean):
                current_mode = "shopping"
                current_category = ""
                continue
            elif re.match(r'^(cutting list|cut list|cut list \+ materials)$', l_clean):
                current_mode = "cutting"
                current_category = ""
                continue
            elif l_clean in ["overview", "legal:", "disclaimer:"]:
                current_mode = None
                continue
                
            # Detect sub-categories (e.g. TABLE, BENCH, FRAME, ROOF, FLOOR, WALLS, SIDING, TRIM)
            if l.isupper() and len(l) < 25 and not re.match(r'^\d+', l) and l not in ["SHOPPING LIST", "CUTTING LIST", "MATERIAL LIST"]:
                current_category = l
                continue
                
            if current_mode is None:
                continue
                
            # Detect Part Letter Tags e.g. (A), (B), (C), (D)
            part_letter = None
            letter_match = re.match(r'^\(([A-Z])\)\s*(.+)', l)
            if letter_match:
                part_letter = f"Part {letter_match.group(1)}"
                l = letter_match.group(2).strip()
                
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["screw", "nail", "shingle", "felt", "drip edge", "roof tacks", "roofing staples"]):
                clean_l = l.lstrip("•").strip()
                
                if current_mode == "shopping":
                    item = parse_material_line(clean_l)
                    if item:
                        if current_category:
                            item["description"] = f"{current_category}: {item['description']}"
                        if item not in materials:
                            materials.append(item)
                elif current_mode == "cutting":
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_l)
                    if match:
                        qty = match.group(1)
                        dims = match.group(2).strip()
                        part_desc = part_letter if part_letter else (f"{current_category} Member" if current_category else "Cut Member")
                        c_item = {
                            "quantity": qty,
                            "dimensions": dims,
                            "description": part_desc
                        }
                        if c_item not in cut_list:
                            cut_list.append(c_item)

    # 4. Dynamic Page-by-Page Construction Step Processing (Strict 1-to-1 Page Alignment)
    step_num = 1
    
    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]
        raw = page.get_text("text") or ""
        cleaned = clean_extracted_text(raw)
        
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        if not lines:
            continue
            
        page_text_lower = cleaned.lower()
        
        # Skip cover, legal disclaimers, and pure shopping/cutting list overview pages
        is_cover_or_legal = page_num <= 3 or any(kw in page_text_lower for kw in ["legal:", "disclaimer:", "all rights reserved", "isbn-"])
        is_pure_list_page = any(re.match(r'^(shopping list|material list|cutting list|cut list)$', l.lower()) for l in lines[:3]) and not any(kw in page_text_lower for kw in ["cut two", "cut nine", "cut four", "assemble", "install", "frame"])
        
        if is_cover_or_legal or is_pure_list_page:
            continue

        instruction_lines = []
        bullet_lines = []
        
        for l in lines:
            if l.startswith("STEP ") or re.match(r'^Page \d+$', l, re.I):
                continue
                
            part_letter = None
            letter_match = re.match(r'^\(([A-Z])\)\s*(.+)', l)
            if letter_match:
                part_letter = f"Part {letter_match.group(1)}"
                l = letter_match.group(2).strip()
                
            if l.startswith("•") or (re.match(r'^\d+[\s\–\-]+', l) and ("cut" in l.lower() or "size" in l.lower() or "sheet" in l.lower() or "plywood" in l.lower() or "treated" in l.lower() or re.search(r'\d+[\′\″\']', l))):
                clean_b = l.lstrip("•").strip()
                if clean_b and clean_b not in bullet_lines:
                    bullet_lines.append(clean_b)
            else:
                instruction_lines.append(l)
                
        exact_page_text = clean_extracted_text(" ".join(instruction_lines))
        if not exact_page_text:
            exact_page_text = clean_extracted_text(" ".join(lines))
            
        if exact_page_text and len(exact_page_text) > 10:
            # STRICT 1-TO-1 PAGE MATCHING:
            # Page N text strictly maps to Page N diagram image (page_{N}_img)
            img_label = f"page_{page_num}_img"
            
            steps.append({
                "step_number": step_num,
                "title": f"STEP {step_num}",
                "page_number": page_num,
                "step_materials": bullet_lines,
                "exact_description": exact_page_text,
                "image_sources": [img_label]
            })
            step_num += 1

    return {
        "project_name": project_name,
        "project_intro": project_intro if project_intro else f"Complete DIY construction guide for {project_name}.",
        "difficulty_level": "Intermediate DIY",
        "finished_dimensions": dimensions,
        "hero_image_source": None,
        "dimension_image_source": None,
        "tools_image_source": None,
        "materials": materials,
        "cut_list": cut_list,
        "tools": [{"name": "Miter Saw"}, {"name": "Circular Saw"}, {"name": "Framing Hammer"}, {"name": "Tape Measure"}, {"name": "Level"}],
        "steps": steps,
        "finishing_instructions": ["Apply primer and two coats of exterior grade paint or stain.", "Caulk all exterior joints with paintable silicone."],
        "missing_images": []
    }
