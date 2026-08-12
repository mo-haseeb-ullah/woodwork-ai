import sys
sys.path.insert(0, r"d:\woodworking_ai")
from pdf_direct_parser import parse_pdf_directly

res = parse_pdf_directly(r"C:\Users\My PC\Downloads\Large-10x12-Lean-To-Shed-Plans.pdf")
print("Project:", res["project_name"])
print("Materials count:", len(res["materials"]))
print("Total Steps count:", len(res["steps"]))
print("\n--- ALL PARSED STEPS ---")
for s in res["steps"]:
    print(f"Step {s['step_number']}: {s['title']} | Img: {s['image_sources']}")
