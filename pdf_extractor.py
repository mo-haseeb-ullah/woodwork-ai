import os
import re
import pymupdf
import zipfile

def create_images_zip(image_paths, zip_output_path):
    with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img_path in image_paths:
            if os.path.exists(img_path):
                arcname = os.path.basename(img_path)
                zipf.write(img_path, arcname=arcname)
    return zip_output_path

def clean_extracted_text(text):
    if not text:
        return ""
    # Remove watermarks, website URLs, Construct101 banners, and page numbers
    text = re.sub(r'Visit\s+www\.Construct101\.com\s+for\s+more\s+DIY\s+Projects\s*(Page\s*\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'www\.Construct101\.com', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Construct101\.com', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Construct101', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Free Woodworking Plans', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Legal:.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Disclaimer:.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'The content of this guide may not be sold.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://\S+', '', text, flags=re.IGNORECASE)
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def extract_from_pdf(pdf_path, output_dir):
    """
    Extracts raw embedded diagram images page-by-page directly from PDF.
    Excludes logo banners, watermarks, cover ads, and small icons.
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    
    extracted_image_paths = []
    text_content = []
    
    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        raw_text = page.get_text("text")
        cleaned = clean_extracted_text(raw_text)
        if cleaned:
            text_content.append(f"--- PAGE {page_num} ---\n" + cleaned)
            
        imgs = page.get_image_info(xrefs=True)
        # Filter out small vector icons / header banners (xref 4 or size < 180x180)
        real_imgs = [im for im in imgs if im.get('xref') != 4 and im.get('width', 0) > 180 and im.get('height', 0) > 180]
        
        if real_imgs:
            # Sort by area to pick the primary construction diagram for this page
            real_imgs.sort(key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
            target_xref = real_imgs[0]['xref']
            try:
                base_image = doc.extract_image(target_xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                img_filename = f"page_{page_num}_img.{image_ext}"
                img_filepath = os.path.join(output_dir, img_filename)
                
                with open(img_filepath, "wb") as f:
                    f.write(image_bytes)
                    
                extracted_image_paths.append(img_filepath)
            except Exception as e:
                print(f"Error extracting image xref {target_xref} on page {page_num}: {e}")
                
    full_text = "\n\n".join(text_content)
    return extracted_image_paths, full_text
