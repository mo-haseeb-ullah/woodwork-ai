import os
import zipfile
import pymupdf
from watermark_remover import remove_watermarks

def extract_from_pdf(pdf_filepath, output_img_dir):
    """
    Extracts text page-by-page and renders high-resolution page diagrams from a PDF file.
    Ensures 100% diagram alignment per page and step without missing any pictures or steps.
    """
    os.makedirs(output_img_dir, exist_ok=True)
    
    doc = pymupdf.open(pdf_filepath)
    full_text_parts = []
    extracted_images = []
    
    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        
        # 1. Extract complete text for this page
        page_text = page.get_text("text") or ""
        if page_text.strip():
            full_text_parts.append(f"--- PAGE {page_num} ---")
            full_text_parts.append(page_text.strip())
            
        # 2. Render exact high-res visual diagram of this page (DPI=150 for crisp quality)
        img_filename = f"scraped_{page_idx}.png"
        img_path = os.path.join(output_img_dir, img_filename)
        
        pix = page.get_pixmap(dpi=150)
        pix.save(img_path)
        
        # Apply watermark/branding removal on page diagram
        try:
            remove_watermarks(img_path)
        except Exception as e:
            print(f"Watermark removal error for {img_path}: {e}")
            
        extracted_images.append(img_path)
        
    extracted_text = "\n\n".join(full_text_parts)
    return extracted_images, extracted_text

def create_images_zip(image_dir_or_list, zip_filepath):
    """
    Bundles all extracted images into a ZIP archive.
    """
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if isinstance(image_dir_or_list, list):
            for img_path in image_dir_or_list:
                if os.path.exists(img_path):
                    arcname = os.path.basename(img_path)
                    zipf.write(img_path, arcname=arcname)
        elif os.path.isdir(image_dir_or_list):
            for root, _, files in os.walk(image_dir_or_list):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.basename(filepath)
                    zipf.write(filepath, arcname=arcname)
    return zip_filepath
