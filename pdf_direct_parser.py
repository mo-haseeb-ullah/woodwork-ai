import os
import re
import pymupdf
from pdf_extractor import clean_extracted_text

def parse_pdf_directly(pdf_filepath):
    """
    Generic Direct PDF Parser (Skipping Shopping List & Cut List Tables):
    - Cover Page: Project Title + Hero Picture (page_1_img) from Page 1.
    - Pages 2 to End: Direct line-by-line page paste with page picture (page_{page_num}_img) and page text lines.
    - Shopping List and Cut List tables are completely skipped as requested.
    """
    doc = pymupdf.open(pdf_filepath)
    
    # 1. Cover Page Hero Picture (Page 1 Image)
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

    # 4. Direct Page-by-Page Line-by-Line Paste (Pages 2 to End)
    # Shopping List and Cut List tables are completely SKIPPED as requested.
    materials = []
    cut_list = []
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
        
        # Filter out pure legal disclaimers
        if any(kw in page_text_lower for kw in ["legal:", "disclaimer:", "all rights reserved", "isbn-"]):
            lines = [l for l in lines if not any(kw in l.lower() for kw in ["legal:", "disclaimer:", "all rights reserved", "isbn-", "reprinting", "prohibited", "prosecuted"])]
            
        if not lines:
            continue

        exact_desc = "\n".join(lines)
        img_label = f"page_{page_num}_img"
        
        steps.append({
            "step_number": step_num,
            "title": f"PAGE {page_num}",
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
        "dimension_image_source": None,
        "tools_image_source": None,
        "materials": [], # SKIPPED
        "cut_list": [],  # SKIPPED
        "tools": [],
        "steps": steps,
        "finishing_instructions": [],
        "missing_images": []
    }
