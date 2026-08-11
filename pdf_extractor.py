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
    Extracts text page-by-page and extracts the ORIGINAL raw embedded picture files from a PDF.
    Does NOT crop images or render page screenshots.
    """
    os.makedirs(output_img_dir, exist_ok=True)
    
    doc = pymupdf.open(pdf_filepath)
    full_text_parts = []
    extracted_images = []
    
    img_counter = 0
    seen_xrefs = set()
    
    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        
        # 1. Extract and sanitize page text
        raw_text = page.get_text("text") or ""
        cleaned_text = clean_extracted_text(raw_text)
        
        if cleaned_text.strip():
            full_text_parts.append(f"--- PAGE {page_num} ---")
            full_text_parts.append(cleaned_text.strip())
            
        # 2. Extract original raw embedded pictures directly from page
        for img_info in page.get_images():
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            
            try:
                base_image = doc.extract_image(xref)
                w = base_image["width"]
                h = base_image["height"]
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Filter out tiny icons or pattern tiles (< 150x150)
                if w >= 150 and h >= 150:
                    img_filename = f"scraped_{img_counter}.{image_ext}"
                    img_path = os.path.join(output_img_dir, img_filename)
                    
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)
                        
                    # Clean watermarks without any cropping
                    try:
                        remove_watermarks(img_path, crop_header_footer=False)
                    except Exception as e:
                        print(f"Watermark removal error: {e}")
                        
                    extracted_images.append(img_path)
                    img_counter += 1
            except Exception as e:
                print(f"Error extracting image xref {xref}: {e}")
                
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
