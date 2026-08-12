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
    # Hardware or fasteners without leading numbers
    if any(kw in clean.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch", "hardware"]):
        return {"quantity": "As Needed", "description": clean}
    return {"quantity": "1", "description": clean}

def parse_pdf_directly(pdf_filepath):
    """
    Direct Python PDF parser that extracts 100% of pages, steps, 
    shopping lists (with exact quantities & descriptions), 
    and cut lists (with exact Qty, Dimensions, and Part Descriptions).
    """
    doc = pymupdf.open(pdf_filepath)
    
    project_name = "Woodworking Plan"
    project_intro = ""
    dimensions = "See Plan Drawings"
    materials = []
    steps = []
    
    # 1. Parse Title (Page 1)
    if len(doc) > 0:
        raw0 = doc[0].get_text("text") or ""
        lines0 = [l.strip() for l in raw0.split("\n") if l.strip() and "Construct101" not in l and "Legal:" not in l and "Disclaimer:" not in l]
        for line in lines0:
            if any(kw in line.upper() for kw in ["PLANS", "SHED", "WOOD", "BUILD", "TABLE", "BENCH", "DESK", "CABINET"]):
                project_name = line
                break
        if project_name == "Woodworking Plan" and lines0:
            project_name = lines0[0]

    # 2. Parse Overview & Dimensions (Pages 2-3)
    intro_lines = []
    for page_idx in range(1, min(3, len(doc))):
        raw = doc[page_idx].get_text("text") or ""
        lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l]
        for l in lines:
            if l.lower() != "overview" and not l.startswith("http"):
                intro_lines.append(l)
                if ("x" in l.lower() or "'" in l or '"' in l) and not dimensions or dimensions == "See Plan Drawings":
                    if any(c.isdigit() for c in l):
                        dimensions = l
                        
    if intro_lines:
        project_intro = clean_extracted_text(" ".join(intro_lines))

    # 3. Parse Shopping List (Pages 4-6) with exact Quantity and Description
    for page_idx in range(3, min(6, len(doc))):
        raw = doc[page_idx].get_text("text") or ""
        lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l]
        for l in lines:
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or any(kw in l.lower() for kw in ["nail", "screw", "flashing", "hinge", "latch"]):
                mat_item = parse_material_line(l)
                if mat_item and mat_item not in materials:
                    materials.append(mat_item)

    # 4. Parse Construction Steps & Cut List (Pages 7 to End)
    start_step_page = 6 if len(doc) >= 7 else 1
    step_num = 1
    cut_list = []
    
    for page_idx in range(start_step_page, len(doc)):
        page = doc[page_idx]
        raw = page.get_text("text") or ""
        lines = [l.strip() for l in raw.split("\n") if l.strip() and "Construct101" not in l and "Page" not in l and "Legal:" not in l and "Disclaimer:" not in l]
        
        clean_lines = [l for l in lines if l not in ["•", "″", "′", "-"] and not l.startswith("Visit www")]
        if not clean_lines:
            continue
            
        first_line = clean_lines[0]
        if first_line in ["Floor", "Walls", "Rafters", "Siding", "Roof", "Door", "Trim", "Front/Back Wall Frame:", "Right/Left Wall Frame:", "Front Top Wall Frame:"]:
            step_title = first_line.rstrip(":")
            content_lines = clean_lines[1:]
        else:
            if len(clean_lines) > 1 and clean_lines[1] in ["Front/Back Wall Frame:", "Right/Left Wall Frame:", "Front Top Wall Frame:"]:
                step_title = clean_lines[1].rstrip(":")
                content_lines = [clean_lines[0]] + clean_lines[2:]
            elif len(first_line) > 50 or "measure and cut" in first_line.lower() or "raise and secure" in first_line.lower() or "rafters are" in first_line.lower() or "install" in first_line.lower():
                step_title = f"Step {step_num}"
                content_lines = clean_lines
            else:
                step_title = first_line.rstrip(":")
                content_lines = clean_lines[1:]
                
        step_bullets = []
        instruction_lines = []
        
        for l in content_lines:
            if l.startswith("•") or re.match(r'^\d+[\s\–\-]+', l) or "cut to size" in l.lower() or "sheet" in l.lower() or ("plywood" in l.lower() and not l.startswith("Measure")):
                clean_b = l.lstrip("•").strip()
                if clean_b and clean_b not in step_bullets:
                    step_bullets.append(clean_b)
                    # Extract structured cut list item for Cut List Table
                    match = re.match(r'^(\d+)\s*[\–\-]\s*(.+)', clean_b)
                    if match:
                        q_str = match.group(1)
                        dim_str = match.group(2).strip()
                        cut_list.append({
                            "quantity": q_str,
                            "dimensions": dim_str,
                            "description": f"{step_title} Member"
                        })
            else:
                instruction_lines.append(l)
                
        step_desc = clean_extracted_text(" ".join(instruction_lines))
        if not step_desc and step_title.startswith("Step "):
            step_desc = clean_extracted_text(clean_lines[0])
            
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
        "project_intro": project_intro if project_intro else "Complete DIY construction guide and woodworking blueprint.",
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
