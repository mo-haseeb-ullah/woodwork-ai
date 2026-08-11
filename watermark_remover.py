import os
from PIL import Image

def remove_watermarks(image_path, crop_header_footer=False):
    """
    Cleans extracted original raw images without performing any cropping.
    """
    if not os.path.exists(image_path):
        return image_path
        
    try:
        if crop_header_footer:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                w, h = img.size
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, w, int(h * 0.075)], fill=(255, 255, 255))
                draw.rectangle([0, int(h * 0.925), w, h], fill=(255, 255, 255))
                img.save(image_path)
        return image_path
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return image_path
