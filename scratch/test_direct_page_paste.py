import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf
import re
from pdf_extractor import clean_extracted_text

pdf_path = r"D:\ETSY\10x10 Barn Shed Plans.pdf"
doc = pymupdf.open(pdf_path)

def parse_pdf_line_by_line_direct(doc):
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
                if clean_t:
                    project_name = clean_t
                    break

    # 3. Process Pages 2 to End Line-by-Line
    page_items = []
    
    for page_idx in range(1, len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]
        raw_text = page.get_text("text") or ""
        cleaned = clean_extracted_text(raw_text)
        
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        if not lines:
            continue
            
        page_items.append({
            "page_number": page_num,
            "image": f"page_{page_num}_img",
            "lines": lines,
            "text_block": "\n".join(lines)
        })

    return {
        "project_name": project_name,
        "hero_image_source": hero_image,
        "page_items": page_items
    }

res = parse_pdf_line_by_line_direct(doc)

print("=== COVER PAGE ===")
print("Project Title:", res["project_name"])
print("Hero Picture (Page 1):", res["hero_image_source"])

print(f"\n=== LINE-BY-LINE PAGE EXTRACTION ({len(res['page_items'])} pages) ===")
for p in res["page_items"][:4]:
    print(f"\n--- PAGE {p['page_number']} ---")
    print(f"Page Picture: {p['image']}")
    print(f"Line 1: {p['lines'][0] if p['lines'] else ''}")
    print(f"Total Lines: {len(p['lines'])}")
