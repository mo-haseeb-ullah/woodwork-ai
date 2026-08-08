import cv2
import numpy as np
import easyocr
import os

# Initialize the EasyOCR reader globally so it doesn't reload the model for every image
# We use 'en' (English). gpu=False ensures it runs on CPU to avoid complex CUDA setups unless available.
try:
    reader = easyocr.Reader(['en'], gpu=False)
except Exception as e:
    print(f"Warning: Failed to initialize EasyOCR. Watermark removal might fail. {e}")
    reader = None

def remove_watermarks(image_path):
    """
    Scans the image for watermarks like 'Construct101' and inpaints them.
    Returns the path to the cleaned image (overwrites the original).
    """
    if reader is None:
        return image_path
        
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            return image_path
            
        # Detect text
        results = reader.readtext(img)
        
        # Create a blank mask for inpainting
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        
        watermark_found = False
        
        # Keywords to look for in the text
        keywords = ['construct', '101', 'www.', '.com', 'copyright', '©']
        
        for (bbox, text, prob) in results:
            text_lower = text.lower()
            
            # Check if this text block is a watermark
            is_watermark = any(kw in text_lower for kw in keywords)
            
            if is_watermark and prob > 0.3:
                watermark_found = True
                
                # Bounding box points from EasyOCR
                # bbox is like: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                pts = np.array(bbox, np.int32)
                pts = pts.reshape((-1, 1, 2))
                
                # Draw a filled polygon on the mask for the bounding box
                cv2.fillPoly(mask, [pts], 255)
        
        if watermark_found:
            # Dilate the mask slightly to ensure edges of the text are covered
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
            
            # Inpaint the original image using the mask
            # INPAINT_TELEA is generally good for small texts and logos
            cleaned_img = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
            
            # Save the cleaned image back
            cv2.imwrite(image_path, cleaned_img)
            print(f"Watermark successfully removed from {image_path}")
            
        return image_path
        
    except Exception as e:
        print(f"Error during watermark removal for {image_path}: {e}")
        return image_path
