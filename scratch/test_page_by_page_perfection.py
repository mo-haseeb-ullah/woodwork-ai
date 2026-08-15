import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
from pdf_direct_parser import parse_pdf_directly

pdf1 = r"D:\ETSY\LARGE 10x12 LEAN TO SHED PLANS.pdf"

print("--- TESTING PAGE-BY-PAGE ALIGNMENT ON LARGE SHED PLANS ---")
res = parse_pdf_directly(pdf1)
print(f"Project Name: {res['project_name']}")
print(f"Shopping List Items: {len(res['materials'])}")
print(f"Cut List Items: {len(res['cut_list'])}")
print(f"Total Step Pages Extracted: {len(res['steps'])}")

for s in res['steps'][:6]:
    print(f"\n--- {s['title']} (Source Page {s.get('page_number')}) ---")
    print(f"Image Source: {s['image_sources']}")
    print(f"Text Snippet: {s['exact_description'][:100]}...")
