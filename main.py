import sys
import os
import json

# Fix for protobuf issue on Python 3.14
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from ai_processor import process_with_ai
from generator import generate_premium_pdf, generate_image_overrides_docx
from image_extractor import extract_images_from_pdf
from docx_extractor import extract_images_from_docx

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        sys.exit(1)
        
    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    
    print("--- STARTING WOODWORKING AI AUTOMATION ---")
    
    try:
        # Step 1: Extract Images from PDF
        print("\n[1/4] Extracting raw images from PDF...")
        page_to_images = extract_images_from_pdf(pdf_path)

        # Step 2: Extract User Overrides from Overrides_V2.docx
        print("\n[2/4] Checking for user-provided images in Overrides_V2.docx...")
        docx_images_dict = extract_images_from_docx("Overrides_V2.docx")

        # Step 3: Send the PDF directly to Gemini API
        print("\n[3/4] Analyzing PDF with Gemini AI...")
        json_output = process_with_ai(pdf_path, API_KEY)
        
        with open("raw_output.json", "w", encoding='utf-8') as f:
            f.write(json_output)
            
        print("\n[4/4] Generating Output Documents...")
        # Step 4: Generate Premium PDF
        generate_premium_pdf(json_output, page_to_images, docx_images_dict, output_filename="Premium_Plan.pdf")
        
        # We regenerate the overrides docx for next time
        generate_image_overrides_docx(json_output, output_filename="Overrides_V2.docx")
        
        print("\n--- ALL TASKS COMPLETED SUCCESSFULLY ---")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
