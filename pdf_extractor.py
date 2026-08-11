import os
import zipfile
from pypdf import PdfReader
from watermark_remover import remove_watermarks

def extract_from_pdf(pdf_filepath, output_img_dir):
    """
    Extracts text and embedded images from a PDF file.
    Saves extracted images to output_img_dir and cleans watermarks.
    Returns (extracted_images_list, extracted_text).
    """
    os.makedirs(output_img_dir, exist_ok=True)
    
    reader = PdfReader(pdf_filepath)
    full_text_parts = []
    extracted_images = []
    
    img_counter = 0
    
    for page_idx, page in enumerate(reader.pages):
        # Extract page text
        page_text = page.extract_text() or ""
        if page_text.strip():
            full_text_parts.append(f"--- PAGE {page_idx + 1} ---")
            full_text_parts.append(page_text.strip())
            
        # Extract images from page
        try:
            for count, image_file_object in enumerate(page.images):
                img_ext = os.path.splitext(image_file_object.name)[1]
                if not img_ext or img_ext.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                    img_ext = '.png'
                    
                img_filename = f"scraped_{img_counter}{img_ext}"
                img_path = os.path.join(output_img_dir, img_filename)
                
                with open(img_path, "wb") as fp:
                    fp.write(image_file_object.data)
                    
                # Filter out tiny clip-art tiles, icons, and thumbnails (< 150x150 px)
                try:
                    from PIL import Image
                    with Image.open(img_path) as im:
                        width, height = im.size
                        if width < 150 or height < 150:
                            fp.close()
                            os.remove(img_path)
                            continue
                except Exception:
                    pass
                    
                # Apply watermark/branding removal on valid extracted images
                try:
                    remove_watermarks(img_path)
                except Exception as e:
                    print(f"Watermark removal error for {img_path}: {e}")
                    
                extracted_images.append(img_path)
                img_counter += 1
        except Exception as img_err:
            print(f"Error extracting images on page {page_idx + 1}: {img_err}")
            
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
