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
    Extracts text page-by-page and crops ONLY the diagram pictures from a PDF file.
    Excludes all page screenshots, titles, text blocks, headers, footers, and links.
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
            
        # 2. Extract ONLY the diagram picture (cropping out page titles, text blocks, and footers)
        img_filename = f"scraped_{page_idx}.png"
        img_path = os.path.join(output_img_dir, img_filename)
        
        blocks = page.get_text('blocks')
        
        # Determine top text boundary (title/instructions end y)
        top_text_ends = [b[3] for b in blocks if 60 <= b[1] <= 350 and not b[4].strip().startswith('---')]
        top_y = max(top_text_ends) if top_text_ends else 70
        
        # Determine bottom text boundary (footer start y)
        footer_starts = [b[1] for b in blocks if b[1] >= 650]
        bot_y = min(footer_starts) if footer_starts else (page.rect.height - 40)
        
        # Crop rectangle isolating the actual diagram picture
        y_top = min(top_y + 5, page.rect.height - 100)
        y_bot = max(bot_y - 5, y_top + 50)
        
        clip_rect = pymupdf.Rect(10, y_top, page.rect.width - 10, y_bot)
        
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
