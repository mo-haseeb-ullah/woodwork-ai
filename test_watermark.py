import shutil
import os
from watermark_remover import remove_watermarks

def run_test():
    source_img = r"C:\Users\Hp\.gemini\antigravity\brain\9fbd7ab6-3b66-41b6-bab9-56e5c690548b\.user_uploaded\uploaded_media_1786099471393.png"
    target_dir = "test_images"
    os.makedirs(target_dir, exist_ok=True)
    
    test_img = os.path.join(target_dir, "test_watermark.png")
    shutil.copy2(source_img, test_img)
    
    print("Running watermark removal...")
    result_path = remove_watermarks(test_img)
    print(f"Done. Cleaned image saved at: {result_path}")

if __name__ == "__main__":
    run_test()
