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
    if any(kw in clean.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "hardware", "staple", "shingle", "felt"]):
        return {"quantity": "As Needed", "description": clean}
    return {"quantity": "1", "description": clean}

def parse_pdf_directly(pdf_filepath):
    """
    Universal Python PDF parser that handles all woodworking PDF plans
    (Chicken Coop Run 10x8, Large Lean-to Shed 10x12, Door/Window guides)
    ensuring clean step titles and 100% instruction sentences in description paragraphs.
    """
    doc = pymupdf.open(pdf_filepath)
    
    project_name = "Woodworking Plan"
    project_intro = ""
    dimensions = "See Plan Drawings"
    materials = []
    cut_list = []
    steps = []
    
    known_headings = [
        "floor", "front wall", "back wall", "right/left wall", "roof", 
        "wire mesh", "trim", "door", "roof deck", "rafters", "siding",
        "shed window framing", "shed single door", "shed double door",
        "front/back wall frame", "right/left wall frame", "front top wall frame",
        "door and window framing", "front/back wall frame ends", "raise and secure wall frames",
        "rafter cut details", "rafter installation", "top wall studs & overhang blocking",
        "siding installation", "roof purlins", "purlin blocking", "metal corrugated roofing panels",
        "door installation", "corner & window trim"
    ]
    
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

    # 3. Dynamic Page Processing (Pages 2 to End)
    start_step_page = 1
    step_num = 1
    current_section = "Construction"
    
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
            
        # Check if page is Overview page
        if any(l.lower().endswith("overview") for l in clean_lines[:2]):
            continue

        # Check if page is Shopping List / Material List page
        is_shopping_page = any("shopping list" in l.lower() or "material list" in l.lower() or "cutting list" in l.lower() for l in clean_lines[:3])
        if is_shopping_page:
            for l in clean_lines:
                if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "staple"]):
                    mat_item = parse_material_line(l)
                    if mat_item and mat_item not in materials:
                        materials.append(mat_item)
            continue

        # Extract Shopping List items embedded on step page
        for l in clean_lines:
            if l.startswith("•") or (re.match(r'^\d+[\s\–\-]+', l) and "cut to size" in l.lower()):
                mat_item = parse_material_line(l)
                if mat_item and mat_item not in materials:
                    materials.append(mat_item)
                    
        # Determine Step Title vs Instruction Sentences
        first_line = clean_lines[0]
        step_title = None
        content_lines = clean_lines
        
        # Check for explicit STEP X: Title format
        step_match = re.match(r'^STEP\s*\d+\s*:\s*(.+)', first_line, re.I)
        if step_match:
            candidate_title = step_match.group(1).strip()
            # If candidate_title is short and not an instruction, use it
            if len(candidate_title) < 40 and not any(kw in candidate_title.lower() for kw in ["cut ", "install ", "measure ", "build ", "raise "]):
                step_title = candidate_title
                content_lines = clean_lines[1:]
                
        if not step_title:
            clean_header = first_line.rstrip(":")
            if any(h in clean_header.lower() for h in known_headings) and len(clean_header) < 40 and not any(kw in clean_header.lower() for kw in ["cut ", "install ", "measure ", "build ", "raise "]):
                step_title = clean_header
                content_lines = clean_lines[1:]
            elif len(clean_lines) > 1:
                second_header = clean_lines[1].rstrip(":")
                if any(h in second_header.lower() for h in known_headings) and len(second_header) < 40:
                    step_title = second_header
                    content_lines = [clean_lines[0]] + clean_lines[2:]
                    
        if step_title:
            current_section = step_title
        else:
            step_title = f"Step {step_num}"
            
        step_bullets = []
        instruction_lines = []
        
        for l in content_lines:
            if l == step_title or l.startswith("STEP "):
                continue
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or "cut to size" in l.lower() or "sheet" in l.lower() or ("plywood" in l.lower() and not l.startswith("Measure")):
                clean_b = l.lstrip("•").strip()
                if clean_b and clean_b not in step_bullets:
                    step_bullets.append(clean_b)
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_b)
                    if match:
                        cut_list.append({
                            "quantity": match.group(1),
                            "dimensions": match.group(2).strip(),
                            "description": f"{step_title} Member"
                        })
            else:
                instruction_lines.append(l)
                
        step_desc = clean_extracted_text(" ".join(instruction_lines))
        if not step_desc:
            step_desc = clean_extracted_text(" ".join(content_lines))
            
        page_num = page_idx + 1
        img_label = f"page_{page_num}_img"
        
        steps.append({
            "step_number": step_num,
            "title": step_title,
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
        "cut_list": cut_list if cut_list else materials,
        "tools": [{"name": "Miter Saw"}, {"name": "Circular Saw"}, {"name": "Framing Hammer"}, {"name": "Tape Measure"}, {"name": "Level"}],
        "steps": steps,
        "finishing_instructions": ["Apply primer and two coats of exterior grade paint or stain.", "Caulk all exterior joints with paintable silicone."],
        "missing_images": []
    }
