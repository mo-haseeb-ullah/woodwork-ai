import os
import time
import json
import requests
import socket

# Force IPv4 to prevent Windows [WinError 10051] on IPv6 Google API
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    try:
        responses = old_getaddrinfo(*args, **kwargs)
        # Try to filter for IPv4
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

    # Upload scraped images (limit to top 30 to prevent payload limits)
    scraped_uris = []
    for img_path in scraped_images[:30]:
        # Extract the base name without extension, e.g., 'scraped_2'
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        print(f"Uploading {base_name}...")
        mime = "image/jpeg"
        
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
    4. Extract the construction `steps` in order. Only extract actual numbered or clearly labeled project steps from the website. DO NOT include introductory text or general advice as a step.
    5. Remove all branding, promotional text, website names.
    6. For the `hero_image`, `dimension_image`, `tools_image`, and each step's `image`:
       - First, check if one of the attached scraped images perfectly matches this location. If so, provide its label (e.g., 'scraped_0') as the `xxx_image_source`.
       - If no scraped image matches, return null.
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
      "steps": [{"step_number": 1, "title": "String", "instructions": ["String"], "image_source": "String or null"}],
      "finishing_instructions": ["String"],
      "missing_images": [{"location_id": "String", "description": "String"}]
    }
    """

    print("Sending data to Gemini API (this may take a minute)...")
    generate_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
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
    
    max_retries = 3
    def make_gemini_request(payload_data):
        for attempt in range(max_retries):
            gen_response = requests.post(generate_url, headers={"Content-Type": "application/json"}, json=payload_data, timeout=(10, 60))
            
            if gen_response.status_code == 429:
                print(f"Rate limited (429). Retrying in 10 seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(10)
                continue
                
            if not gen_response.ok:
                print("Gemini API Error:", gen_response.text)
            gen_response.raise_for_status()
            return gen_response.json()
        raise Exception("Max retries exceeded")

    print("Pass 1: Extracting data...")
    result1 = make_gemini_request(payload)
    first_json = result1["candidates"][0]["content"]["parts"][0]["text"]
    
    print("Pass 2: Validating extraction...")
    verify_prompt = f"""
    Here is the JSON you extracted:
    {first_json}
    
    Double-check this JSON against the original SCRAPED TEXT provided earlier.
    1. Did you miss any materials or tools mentioned in the text? If so, add them.
    2. Are there any repeated steps or steps that include non-instructional text (like prep work)? If so, fix them.
    3. Ensure the output strictly follows the schema.
    
    Return the final, perfectly corrected JSON object.
    """
    
    parts.append({"text": verify_prompt})
    payload["contents"] = [{"parts": parts}]
    
    result2 = make_gemini_request(payload)
    final_json = result2["candidates"][0]["content"]["parts"][0]["text"]
    
    return final_json
