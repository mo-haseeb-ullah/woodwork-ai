import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import os
import pymupdf

pdf_path = r"D:\ETSY\10x10 Barn Shed Plans.pdf"
doc = pymupdf.open(pdf_path)

output_dir = r"D:\woodworking_ai\scratch\test_multi_imgs"
os.makedirs(output_dir, exist_ok=True)

multi_img_pages = []

for page_idx, page in enumerate(doc):
    page_num = page_idx + 1
    imgs = page.get_image_info(xrefs=True)
    real_imgs = [im for im in imgs if im.get('xref') != 4 and im.get('width', 0) > 150 and im.get('height', 0) > 150]
    
    # Sort real images vertically by top y-coordinate (bbox[1])
    real_imgs.sort(key=lambda x: x.get('bbox', [0,0,0,0])[1])
    
    if len(real_imgs) > 1:
        multi_img_pages.append((page_num, len(real_imgs)))
        print(f"Page {page_num} has {len(real_imgs)} diagram images!")

print(f"\nTotal Pages with Multiple Images: {len(multi_img_pages)}")
