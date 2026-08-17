import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO

def clean_text(text):
    if not text: return ""
    import re
    # Remove Ana White branding variations
    text = re.sub(r'(?i)free plans? by ANA-WHITE\.com', '', text)
    text = re.sub(r'(?i)free plans? by ANA WHITE', '', text)
    text = re.sub(r'(?i)by ANA-WHITE\.com', '', text)
    text = re.sub(r'(?i)\|? ?ana white', '', text)
    text = re.sub(r'(?i)free plans? by', '', text)
    text = re.sub(r'(?i)ana-white\.com', '', text)
    return text.strip(" -|\n\t")

def parse_ana_white_url(url, t_id):
    """
    Directly parses an Ana White URL without using Gemini AI.
    Returns the exact JSON schema expected by generator.py.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    main_content = soup.find('main') or soup
    
    # 1. Project Title
    raw_title = soup.title.string if soup.title else ""
    project_title = clean_text(raw_title)
    if not project_title:
        h1 = main_content.find('h1')
        project_title = clean_text(h1.get_text(strip=True)) if h1 else "Woodworking Project"
        
    # Image downloader helper
    scraped_images = []
    save_dir = "scraped_images"
    os.makedirs(save_dir, exist_ok=True)
    
    def download_image(img_tag):
        if not img_tag:
            return None
        img_url = img_tag.get('data-lazy-src') or img_tag.get('data-src') or img_tag.get('src')
        if not img_url:
            return None
            
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            parsed_url = urlparse(url)
            img_url = f"{parsed_url.scheme}://{parsed_url.netloc}{img_url}"
            
        try:
            img_res = requests.get(img_url, headers=headers, timeout=(5, 15))
            if img_res.status_code == 200:
                with Image.open(BytesIO(img_res.content)) as pil_img:
                    if pil_img.mode in ('RGBA', 'P', 'LA'):
                        pil_img = pil_img.convert('RGB')
                    elif pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                        
                    idx = len(scraped_images)
                    filename = f"scraped_{t_id}_{idx}.jpg"
                    filepath = os.path.join(save_dir, filename)
                    pil_img.save(filepath, format='JPEG', quality=85)
                    scraped_images.append(filepath)
                    return f"scraped_{t_id}_{idx}"
        except Exception:
            pass
        return None

    # 2. Hero Image
    # usually inside a div with class 'field--name-field-image' or the first large image
    hero_image_source = None
    hero_field = main_content.find(class_='field--name-field-image')
    if hero_field:
        hero_img = hero_field.find('img')
        hero_image_source = download_image(hero_img)
        
    if not hero_image_source:
        hero_image_source = download_image(main_content.find('img')) # Fallback to first image

    # 3. Dimensions Section
    dimensions_str = ""
    dimension_image_source = None
    dim_label = main_content.find(string=lambda t: t and "Dimensions" in t)
    if dim_label and dim_label.parent:
        dim_parent = dim_label.parent.parent
        # Sometimes dimensions are just text, sometimes an image
        dim_img = dim_parent.find('img')
        if dim_img:
            dimension_image_source = download_image(dim_img)
        else:
            # Let's check next sibling
            ns = dim_parent.find_next_sibling()
            if ns:
                dim_img2 = ns.find('img')
                if dim_img2:
                    dimension_image_source = download_image(dim_img2)
                dimensions_str = ns.get_text(separator=' ', strip=True)

    # 4. Shopping List & Cut List
    import re
    materials = []
    cut_list = []
    
    def extract_list_by_class(class_keywords):
        items = []
        fields = main_content.find_all(class_=lambda c: c and any(k in c.lower() for k in class_keywords))
        for field in fields:
            # We want the container field, usually starts with 'field--name-field'
            if 'field--name-field' in ' '.join(field.get('class', [])):
                items_container = field.find(class_='field--item') or field.find(class_='field--items')
                if items_container:
                    ul = items_container.find('ul')
                    if ul:
                        items = [li.get_text(strip=True) for li in ul.find_all('li')]
                    else:
                        items = [line.strip() for line in items_container.get_text(separator='\n').split('\n') if line.strip()]
                break # Found the first matching section
        return items

    def parse_item_qty_desc(item_text):
        match_dash = re.match(r"^([\d\s/]+)\s*-\s*(.*)", item_text)
        if match_dash:
            return match_dash.group(1).strip(), match_dash.group(2).strip()
        
        match_space = re.match(r"^([\d]+)\s+([a-zA-Z].*)", item_text)
        if match_space:
            return match_space.group(1).strip(), match_space.group(2).strip()
            
        return "", item_text

    raw_shopping = extract_list_by_class(['shoppinglist', 'materials', 'shopping-list'])
    for item in raw_shopping:
        qty, desc = parse_item_qty_desc(item)
        materials.append({"quantity": qty, "description": desc})
        
    raw_cut = extract_list_by_class(['cutlist', 'cut-list', 'cut_list'])
    for item in raw_cut:
        qty, desc = parse_item_qty_desc(item)
        cut_list.append({"quantity": qty, "dimensions": "", "description": desc})

    # 5. Steps
    steps = []
    step_headers = main_content.find_all(lambda tag: tag.name in ['h2','h3','h4'] and 'step' in tag.get_text(strip=True).lower())
    
    for i, h in enumerate(step_headers):
        step_title = h.get_text(strip=True)
        step_desc = []
        step_images = []
        
        next_node = h.find_next_sibling()
        while next_node and next_node.name not in ['h2','h3','h4']:
            if next_node.name in ['p', 'div']:
                text = next_node.get_text(separator='\n', strip=True)
                if text: 
                    step_desc.append(text)
            
            for img in next_node.find_all('img') if next_node.name != 'img' else [next_node]:
                src = download_image(img)
                if src: 
                    step_images.append(src)
                
            next_node = next_node.find_next_sibling()
            
        steps.append({
            "step_number": i + 1,
            "title": step_title,
            "exact_description": "\n".join(step_desc),
            "image_sources": step_images
        })

    # Return structured JSON directly
    
    # 6. Description / Overview / Intro
    intro_parts = []
    summary_field = main_content.find(class_='field--name-field-summary')
    if summary_field:
        intro_parts.append(summary_field.get_text(separator='\n', strip=True))
        
    author_notes = main_content.find(class_='field--name-field-authornotes')
    if author_notes:
        intro_parts.append(author_notes.get_text(separator='\n', strip=True))
        
    if not intro_parts:
        body_field = main_content.find(class_='field--name-body')
        if body_field:
            intro_parts.append(body_field.get_text(separator='\n', strip=True))
            
    project_intro = clean_text("\n\n".join(intro_parts))
        
    # Exclude "Add Brag Post" if it slipped in
    if project_intro.lower().replace('\n', '').strip() == "add brag post":
        project_intro = ""
    else:
        # Sometimes 'Add Brag Post' is prepended to the real text, strip it
        project_intro = project_intro.replace('Add Brag Post', '').strip()

    # 7. Tools
    tools_list = []
    tools_field = main_content.find(class_='field--name-field-tools')
    if tools_field:
        imgs = tools_field.find_all('img')
        for img in imgs:
            alt = img.get('alt')
            if alt:
                tools_list.append(alt)
                
    # 8. Finishing / Preparation Instructions
    finishing_instructions = []
    
    prep_field = main_content.find(class_=lambda c: c and 'preparation' in c.lower())
    if prep_field:
        lines = prep_field.get_text(separator='\n').split('\n')
        finishing_instructions.extend([line.strip() for line in lines if line.strip() and "instructions" not in line.lower()])
        
    finish_field = main_content.find(class_=lambda c: c and 'finishing' in c.lower())
    if finish_field:
        # Avoid duplicate text if finishing and preparation are in the same container
        lines = finish_field.get_text(separator='\n').split('\n')
        for line in lines:
            cl = line.strip()
            if cl and "instructions" not in cl.lower() and cl not in finishing_instructions:
                finishing_instructions.append(cl)

    return {
        "project_title": project_title,
        "project_intro": project_intro,
        "description": project_intro,
        "finished_dimensions": dimensions_str,
        "hero_image_source": hero_image_source,
        "dimension_image_source": dimension_image_source,
        "tools_image_source": None,
        "materials": materials,
        "cut_list": cut_list,
        "tools": tools_list,
        "steps": steps,
        "finishing_instructions": finishing_instructions
    }
