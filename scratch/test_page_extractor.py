import sys
import os
import pymupdf

pdf_path = r"C:\Users\My PC\Downloads\Large-10x12-Lean-To-Shed-Plans.pdf"
doc = pymupdf.open(pdf_path)
out_dir = r"d:\woodworking_ai\test_page_extracted"
os.makedirs(out_dir, exist_ok=True)

print("=== EXACT PAGE-BY-PAGE IMAGE EXTRACTION ===")
for i, page in enumerate(doc):
    page_num = i + 1
    imgs = page.get_image_info(xrefs=True)
    real_imgs = [im for im in imgs if im['xref'] != 4 and im.get('width', 0) > 150 and im.get('height', 0) > 150]
    
    if real_imgs:
        target_xref = real_imgs[0]['xref']
        base_img = doc.extract_image(target_xref)
        ext = base_img['ext']
        img_filename = f"page_{page_num}_img.{ext}"
        img_path = os.path.join(out_dir, img_filename)
        with open(img_path, 'wb') as f:
            f.write(base_img['image'])
        print(f"Page {page_num}: Extracted xref {target_xref} -> {img_filename} ({base_img['width']}x{base_img['height']})")
    else:
        print(f"Page {page_num}: No diagram image found")
