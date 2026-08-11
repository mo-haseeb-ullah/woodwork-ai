import os
import re
import zipfile
import pymupdf
from watermark_remover import remove_watermarks

def clean_extracted_text(text):
    """
    Removes branding, website links, copyright notices, author details, 
    legal boilerplate, and the word 'Free' from extracted PDF text.
    """
    if not text:
        return ""
        
    # Remove URLs, website names, and links
    text = re.sub(r'https?://\S+|www\.\S+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Construct101\.com|Construct101|construct101', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Visit\s+.*?for\s+more\s+DIY\s+Projects', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Free\s+Woodworking\s+Plans|Free\s+Plans', '', text, flags=re.IGNORECASE)
    
    # Remove Legal & Disclaimer boilerplate blocks
    text = re.sub(r'Legal:\s*The content of this guide.*?prosecuted\.', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Disclaimer:\s*Every attempt has been made.*?\.', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up empty multiple line gaps
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def extract_from_pdf(pdf_filepath, output_img_dir):
    """
    Extracts text page-by-page and crops ONLY the pure diagram picture graphics from a PDF file.
    Excludes all text paragraphs, titles, headers, footers, and links from the extracted picture.
    """
    os.makedirs(output_img_dir, exist_ok=True)
    
    doc = pymupdf.open(pdf_filepath)
    full_text_parts = []
    extracted_images = []
    
    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        
        # 1. Extract and sanitize page text
        raw_text = page.get_text("text") or ""
        cleaned_text = clean_extracted_text(raw_text)
        
        if cleaned_text.strip():
            full_text_parts.append(f"--- PAGE {page_num} ---")
            full_text_parts.append(cleaned_text.strip())
            
        # 2. Crop ONLY the pure diagram image graphic (excluding page text, titles, headers, footers)
        img_filename = f"scraped_{page_idx}.png"
        img_path = os.path.join(output_img_dir, img_filename)
        
        info = page.get_image_info(xrefs=True)
        # Filter for main step diagram image bboxes (width > 60, height > 60, y0 > 50)
        diagram_info = [
            item for item in info 
            if (item['bbox'][3] - item['bbox'][1]) > 60 
            and (item['bbox'][2] - item['bbox'][0]) > 60 
            and item['bbox'][1] > 50
        ]
        
        if diagram_info:
            bbox = pymupdf.Rect()
            for item in diagram_info:
                bbox.include_rect(item['bbox'])
            # Add 4px padding safely
            clip_rect = pymupdf.Rect(
                max(0, bbox.x0 - 4), 
                max(0, bbox.y0 - 4), 
                min(page.rect.width, bbox.x1 + 4), 
                min(page.rect.height, bbox.y1 + 4)
            )
            pix = page.get_pixmap(dpi=150, clip=clip_rect)
        else:
            # Fallback for text-only pages: crop central area excluding top header & bottom footer
            blocks = page.get_text('blocks')
            top_text_ends = [b[3] for b in blocks if 60 <= b[1] <= 350 and not b[4].strip().startswith('---')]
            top_y = max(top_text_ends) if top_text_ends else 70
            footer_starts = [b[1] for b in blocks if b[1] >= 650]
            bot_y = min(footer_starts) if footer_starts else (page.rect.height - 40)
            
            clip_rect = pymupdf.Rect(10, min(top_y + 5, page.rect.height - 100), page.rect.width - 10, max(bot_y - 5, top_y + 50))
            pix = page.get_pixmap(dpi=150, clip=clip_rect)
            
        pix.save(img_path)
        
        # 3. Apply top & bottom header/footer whitewashing for safety
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
