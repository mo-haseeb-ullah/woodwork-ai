import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
from pdf_direct_parser import parse_pdf_directly

res = parse_pdf_directly(r"D:\Plans\Chicken-Coop-Run-10x8.pdf")
print("Project Name:", res["project_name"])
print("Shopping List count:", len(res["materials"]))
print("Steps count:", len(res["steps"]))
print("\n--- PARSED STEPS ---")
for s in res["steps"]:
    print(f"Step {s['step_number']}: {s['title']} | Img: {s['image_sources']} | Desc: {s['exact_description']}")
