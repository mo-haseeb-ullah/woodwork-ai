import os
import re
import pymupdf
from pdf_extractor import clean_extracted_text

def parse_pdf_directly(pdf_filepath):
    """
    Universal Spatial PDF Parser (Multi-Image Support):
    - Supports pages with MULTIPLE pictures (page_N_img_1, page_N_img_2, etc.).
    - Cover Page: Project Title + Hero Picture (page_1_img).
    - Spatial Placement: Places text above/below images in top-to-bottom vertical order.
    - Highlights 'Material List', 'Shopping List', 'Cutting List', 'Cut List', and section titles as BOLD Headings.
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

    # 3. Spatial Page-by-Page Content Extraction (Pages 2 to End)
    steps = []
    step_num = 1
    
    for p_idx in range(1, len(doc)):
        page_num = p_idx + 1
        page = doc[p_idx]
        
        # Identify ALL diagram images on this page sorted top-to-bottom
        img_info_list = page.get_image_info(xrefs=True)
        real_imgs = [im for im in img_info_list if im.get('xref') != 4 and im.get('width', 0) > 140 and im.get('height', 0) > 140]
        real_imgs.sort(key=lambda x: x.get('bbox', [0,0,0,0])[1])
        
        # Build image source labels for this page
        img_labels = []
        if real_imgs:
            for sub_idx in range(len(real_imgs)):
                img_labels.append(f"page_{page_num}_img_{sub_idx + 1}")
        else:
            img_labels.append(f"page_{page_num}_img")
            
        img_y0 = real_imgs[0]["bbox"][1] if real_imgs else None

        blocks = page.get_text("blocks")
        lines_above = []
        lines_below = []
        
        for b in blocks:
            if b[6] == 0: # text block
                b_text = b[4].strip()
                if not b_text:
                    continue
                b_y1 = b[3]
                
                cleaned_block = clean_extracted_text(b_text)
                block_lines = [l.strip() for l in cleaned_block.split("\n") if l.strip()]
                block_lines = [l for l in block_lines if not any(kw in l.lower() for kw in ["legal:", "disclaimer:", "all rights reserved", "isbn-", "reprinting", "prohibited", "prosecuted"])]
                
                if not block_lines:
                    continue
                    
                if img_y0 is not None:
                    if b_y1 <= img_y0 + 20:
                        lines_above.extend(block_lines)
                    else:
                        lines_below.extend(block_lines)
                else:
                    lines_below.extend(block_lines)

        steps.append({
            "step_number": step_num,
            "page_number": page_num,
            "lines_above": lines_above,
            "lines_below": lines_below,
            "image_sources": img_labels
        })
        step_num += 1

    return {
        "project_name": project_name,
        "difficulty_level": "Intermediate DIY",
        "finished_dimensions": "See Plan Drawings",
        "hero_image_source": hero_image,
        "dimension_image_source": None,
        "tools_image_source": None,
        "materials": [],
        "cut_list": [],
        "tools": [],
        "steps": steps,
        "finishing_instructions": [],
        "missing_images": []
    }
