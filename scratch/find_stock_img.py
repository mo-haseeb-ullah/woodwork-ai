import os
import glob

matches = []
for root, dirs, files in os.walk(r"d:\woodworking_ai"):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            matches.append((full_path, size))

for p, s in matches:
    if "extracted_images" not in p and "test_raw_pics" not in p:
        print(f"File: {p} (Size: {s} bytes)")
