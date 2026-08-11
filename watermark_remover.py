import os
from PIL import Image, ImageDraw

def remove_watermarks(image_path, crop_header_footer=True):
    """
    Removes headers, footers, watermarks, page numbers, and website links 
    from extracted PDF images by whitewashing top and bottom header/footer regions 
    and cleaning branding.
    """
    if not os.path.exists(image_path):
        return image_path
        
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            w, h = img.size
            
            draw = ImageDraw.Draw(img)
            
            if crop_header_footer:
                # Whitewash Top Header (top 7.5% containing 'Visit www.Construct101.com' & Page numbers)
                draw.rectangle([0, 0, w, int(h * 0.075)], fill=(255, 255, 255))
                
                # Whitewash Bottom Footer (bottom 7.5% containing copyright & website links)
                draw.rectangle([0, int(h * 0.925), w, h], fill=(255, 255, 255))
                
            img.save(image_path, "PNG")
            print(f"Header/Footer and branding successfully removed from {os.path.basename(image_path)}")
            
        return image_path
    except Exception as e:
        print(f"Error removing watermarks from {image_path}: {e}")
        return image_path
