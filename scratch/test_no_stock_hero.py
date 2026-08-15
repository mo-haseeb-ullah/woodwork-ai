import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
import os
import pymupdf
from pdf_direct_parser import parse_pdf_directly
from pdf_extractor import extract_from_pdf
from generator import generate_premium_pdf

pdf_path = r"D:\Plans\10x10-Barn-Shed-Plans.pdf"
output_dir = r"D:\woodworking_ai\scratch\test_clean_docx"
os.makedirs(output_dir, exist_ok=True)

print("Extracting images from PDF...")
img_paths, full_text = extract_from_pdf(pdf_path, output_dir)
print(f"Extracted {len(img_paths)} diagram images directly from PDF pages.")

print("Parsing PDF data directly...")
plan_data = parse_pdf_directly(pdf_path)

docx_path = os.path.join(output_dir, "Clean_Barn_Shed_Plan.docx")
print("Generating Word document...")
generate_premium_pdf(plan_data, output_filename=docx_path, custom_img_dir=output_dir)

print(f"SUCCESS! DOCX generated cleanly at: {docx_path}")
