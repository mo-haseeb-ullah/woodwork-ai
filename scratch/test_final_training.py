import sys
sys.path.insert(0, r"d:\woodworking_ai")
sys.stdout.reconfigure(encoding='utf-8')
from pdf_direct_parser import parse_pdf_directly

pdf1 = r"D:\ETSY\LARGE 10x12 LEAN TO SHED PLANS.pdf"
pdf2 = r"D:\ETSY\8x10 Chicken Coop Plans.pdf"

print("--- TESTING PDF 1: LARGE SHED ---")
res1 = parse_pdf_directly(pdf1)
print("PROJECT NAME:", res1["project_name"])
print("SHOPPING LIST ITEMS:", len(res1["materials"]))
for m in res1["materials"][:5]:
    print(" -", m)
print("CUT LIST ITEMS:", len(res1["cut_list"]))
for c in res1["cut_list"][:5]:
    print(" -", c)
print("FIRST 3 STEP HEADINGS:")
for s in res1["steps"][:3]:
    print(" - Title:", s["title"])

print("\n--- TESTING PDF 2: 8x10 CHICKEN COOP ---")
res2 = parse_pdf_directly(pdf2)
print("PROJECT NAME:", res2["project_name"])
print("SHOPPING LIST ITEMS:", len(res2["materials"]))
for m in res2["materials"][:5]:
    print(" -", m)
print("CUT LIST ITEMS:", len(res2["cut_list"]))
for c in res2["cut_list"][:5]:
    print(" -", c)
print("FIRST 3 STEP HEADINGS:")
for s in res2["steps"][:3]:
    print(" - Title:", s["title"])
