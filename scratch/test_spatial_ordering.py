import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re
from pdf_extractor import clean_extracted_text

pdf_path = r"D:\ETSY\10x10 Barn Shed Plans.pdf"
doc = pymupdf.open(pdf_path)

def parse_spatial_page_content(page):
    img_y0 = None
    img_y1 = None
    
    img_info_list = page.get_image_info(xrefs=True)
    if img_info_list:
        main_img = max(img_info_list, key=lambda img: (img["bbox"][2]-img["bbox"][0]) * (img["bbox"][3]-img["bbox"][1]))
        if (main_img["bbox"][2]-main_img["bbox"][0]) > 100 and (main_img["bbox"][3]-main_img["bbox"][1]) > 100:
            img_y0 = main_img["bbox"][1]
            img_y1 = main_img["bbox"][3]

    blocks = page.get_text("blocks")
    
    lines_above = []
    lines_below = []
    
    for b in blocks:
        if b[6] == 0:
            b_text = b[4].strip()
            if not b_text:
                continue
            b_y0 = b[1]
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

    return lines_above, lines_below

for p_idx in range(min(10, len(doc))):
    p_num = p_idx + 1
    above, below = parse_spatial_page_content(doc[p_idx])
    print(f"\n--- PAGE {p_num} ---")
    print(f"  Lines Above Image: {len(above)}")
    if above:
        print(f"    First line above: {above[0]}")
    print(f"  Lines Below Image: {len(below)}")
    if below:
        print(f"    First line below: {below[0]}")
