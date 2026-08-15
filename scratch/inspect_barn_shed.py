import sys
sys.stdout.reconfigure(encoding='utf-8')
import pymupdf

pdf_path = r"D:\Plans\10x10-Barn-Shed-Plans.pdf"
doc = pymupdf.open(pdf_path)

print(f"Total Pages in {pdf_path}: {len(doc)}")
for i, page in enumerate(doc):
    text = page.get_text("text") or ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    print(f"\n--- PAGE {i+1} ---")
    print("\n".join(lines[:15]))
