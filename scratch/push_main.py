import subprocess
import sys

git_exe = r"C:\git\cmd\git.exe"

print("Checking out main branch...")
subprocess.run([git_exe, "checkout", "main"], check=True)

print("Updating ai_processor.py on main with 503 retries & gemini-2.0-flash...")
code = '''import os
import time
import json
import requests
import socket

old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    try:
        responses = old_getaddrinfo(*args, **kwargs)
        ipv4_res = [res for res in responses if res[0] == socket.AF_INET]
        return ipv4_res if ipv4_res else responses
    except Exception:
        return old_getaddrinfo(*args, **kwargs)
socket.getaddrinfo = new_getaddrinfo

def process_with_ai(scraped_text, api_key, scraped_images=None):
    if scraped_images is None:
        scraped_images = []
        
    print("Uploading scraped images to Gemini REST API...")
    upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
    
    def upload_file_to_gemini(filepath, mime_type):
        file_size = os.path.getsize(filepath)
        headers = {
            "X-Goog-Upload-Command": "start, upload, finalize",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": mime_type
        }
        with open(filepath, "rb") as f:
            file_data = f.read()
            
        res = requests.post(upload_url, headers=headers, data=file_data, timeout=(10, 60))
        res.raise_for_status()
        return res.json()["file"]["uri"]

    scraped_uris = []
    for img_path in scraped_images[:45]:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        mime = "image/jpeg"
        if img_path.lower().endswith(".png"):
            mime = "image/png"
        
        try:
            uri = upload_file_to_gemini(img_path, mime)
            scraped_uris.append((base_name, uri, img_path, mime))
        except Exception as e:
            print(f"Failed to upload {img_path}: {e}")

    prompt = """
    You are an expert woodworking assistant. I have provided the scraped text from a woodworking blog post.
    I have also attached several images scraped from the original project website, labeled as 'scraped_0', 'scraped_1', etc.
    
    Your job is to read the text and extract/structure this data according to these EXACT rules. DO NOT hallucinate or add anything from your own knowledge.
    1. Extract the Project Name, Difficulty Level, and Finished Dimensions.
    2. Write a short `project_intro`.
    3. Extract the complete Shopping List (Materials), Cut list, and Tools list. If there is no explicit 'Tools' heading, carefully read the text to find which tools are mentioned. Do NOT guess or hallucinate tools that are not mentioned.
    4. First, identify the total number of steps in the source text. You must ensure your final JSON array contains exactly that many steps. Do not skip any. Extract ALL construction `steps` in order, exactly as they appear in the original text. DO NOT rewrite, summarize, or alter the explanation. You must copy the text for each step character-for-character into a single `exact_description` string. DO NOT use bulleted lists for step descriptions unless the original text explicitly used bullets.
    5. CRITICAL: Remove all branding, promotional text, website names, copyright notices, author names (names of persons/creators), watermarks (e.g. Construct101), logo names, the word "Free" (or phrases like "Free Woodworking Plans"), and links from the extracted text. Give me only pure woodworking plans.
    6. For the `hero_image`, `dimension_image`, `tools_image`, and each step's `image`:
       - First, check if one or more of the attached scraped images matches this location. If so, provide their labels (e.g., 'scraped_0') as a list of strings for `image_sources` or `xxx_image_source`.
       - If no scraped image matches, return an empty list or null.
    7. If an image is completely missing from the scraped images, list it in `missing_images`.
    8. Extract any Finishing Instructions, Preparation Instructions, or final sanding/painting/staining steps into a list of strings called `finishing_instructions`.
    
    You MUST return the output as a valid JSON object matching exactly this structure. ONLY include these exact keys:
    {
      "project_name": "String",
      "project_intro": "String",
      "difficulty_level": "String",
      "finished_dimensions": "String",
      "hero_image_source": "String or null",
      "dimension_image_source": "String or null",
      "tools_image_source": "String or null",
      "materials": [{"quantity": "String", "description": "String"}],
      "cut_list": [{"quantity": "String", "dimensions": "String", "description": "String"}],
      "tools": [{"name": "String"}],
      "steps": [{"step_number": 1, "title": "String", "exact_description": "String", "image_sources": ["String"]}],
      "finishing_instructions": ["String"],
      "missing_images": [{"location_id": "String", "description": "String"}]
    }
    """

    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
    
    parts = [
        {"text": "--- START SCRAPED TEXT ---\n" + scraped_text + "\n--- END SCRAPED TEXT ---\n"}
    ]
    
    for base_name, uri, _, mime in scraped_uris:
        parts.append({"text": f"Image '{base_name}':"})
        parts.append({"file_data": {"mime_type": mime, "file_uri": uri}})
        
    parts.append({"text": prompt})
    
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }
    
    max_retries = 4
    def make_gemini_request(payload_data):
        last_err = None
        for model in models_to_try:
            curr_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            for attempt in range(max_retries):
                try:
                    gen_response = requests.post(curr_url, headers={"Content-Type": "application/json"}, json=payload_data, timeout=(10, 60))
                    
                    if gen_response.status_code in [503, 500, 502, 504, 429]:
                        wait_sec = 3 * (attempt + 1)
                        print(f"Gemini API returned {gen_response.status_code} ({model}). Retrying in {wait_sec}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(wait_sec)
                        continue
                        
                    if gen_response.status_code in [404, 400] and attempt == 0:
                        print(f"Model {model} returned {gen_response.status_code}, trying next fallback model...")
                        break
                        
                    if not gen_response.ok:
                        print("Gemini API Error:", gen_response.text)
                    gen_response.raise_for_status()
                    return gen_response.json()
                except Exception as e:
                    last_err = e
                    time.sleep(2)
                    
        raise Exception(f"Google Gemini API is temporarily busy (503 Service Unavailable). Please click 'Generate Blueprint' again in a few seconds. ({last_err})")

    print("Pass 1: Extracting data...")
    result1 = make_gemini_request(payload)
    first_json = result1["candidates"][0]["content"]["parts"][0]["text"]
    
    print("Pass 2: Validating extraction...")
    verify_prompt = f"""
    Here is the JSON you extracted:
    {first_json}
    
    Double-check this JSON against the original SCRAPED TEXT provided earlier.
    1. Did you miss any materials or tools mentioned in the text? If so, add them.
    2. Did you skip or summarize any steps from the original text? If so, restore them in full. The user wants ALL steps exactly as they appear in the original text, copied word-for-word into `exact_description`.
    3. Ensure the output strictly follows the schema.
    
    Return the final, perfectly corrected JSON object.
    """
    
    parts.append({"text": verify_prompt})
    payload["contents"] = [{"parts": parts}]
    
    try:
        result2 = make_gemini_request(payload)
        final_json = result2["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Pass 2 verification failed ({e}), using Pass 1 output...")
        final_json = first_json
        
    return final_json
'''

with open("ai_processor.py", "w", encoding="utf-8") as f:
    f.write(code)

subprocess.run([git_exe, "add", "ai_processor.py"], check=True)
subprocess.run([git_exe, "commit", "-m", "Fix Gemini 503 error on main branch by updating model endpoints to gemini-2.0-flash with automatic retries"], check=False)

print("Pushing main to origin on GitHub...")
res = subprocess.run([git_exe, "push", "origin", "main"], capture_output=True, text=True)
print("PUSH STDOUT:", res.stdout)
print("PUSH STDERR:", res.stderr)

print("Switching back to develop branch...")
subprocess.run([git_exe, "checkout", "develop"], check=True)
print("SUCCESSFULLY DONE!")
