import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO

def clean_text(text):
    if not text: return ""
    # Aggressively remove Ana White branding and the word "free"
    text = re.sub(r'(?i)free plans? by ANA-WHITE\.com', '', text)
    text = re.sub(r'(?i)free plans? by ANA WHITE', '', text)
    text = re.sub(r'(?i)by ANA-WHITE\.com', '', text)
    text = re.sub(r'(?i)\|? ?ana white', '', text)
    text = re.sub(r'(?i)free plans? by', '', text)
    text = re.sub(r'(?i)ana-white\.com', '', text)
    text = re.sub(r'(?i)\bfree\b', '', text)
    text = re.sub(r'(?i)\bfree diy\b', '', text)
    # Clean up multiple spaces or lingering hyphens/punctuation from removals
    text = re.sub(r'\s+', ' ', text)
    return text.strip(" -|\n\t,.")

def ai_summarize_overview(text):
    if not text: return ""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return text
    
    try:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = f"Summarize this woodworking project overview in 3 to 4 lines. Make it sound professional, engaging, and compact. Completely remove any mention of 'Ana White', 'free', 'plans', or 'brag post'. Return ONLY the summarized text without quotes or markdown formatting. Here is the text:\n\n{text}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        resp = requests.post(api_url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        print(f"AI summarization API returned status {resp.status_code}")
        return text
    except Exception as e:
        print(f"AI summarization failed: {e}")
        return text

def normalize_dashes(text):
    """Replace en-dash, em-dash, figure dash with regular hyphen."""
    return text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2012', '-')

def parse_item_qty_desc(item_text):
    """Parse a list item into quantity and description."""
    normalized = normalize_dashes(item_text)
    
    match_dash = re.match(r"^([\d\s/]+)\s*-\s*(.*)", normalized)
    if match_dash:
        return match_dash.group(1).strip(), match_dash.group(2).strip()
    
    match_space = re.match(r"^([\d]+)\s+([a-zA-Z].*)", normalized)
    if match_space:
        return match_space.group(1).strip(), match_space.group(2).strip()
        
    return "", item_text

def parse_cut_item(item_text):
    """Parse a cut list item into qty, board type, and cut dimension."""
    normalized = normalize_dashes(item_text)
    qty, desc = parse_item_qty_desc(normalized)
    
    if '@' in desc:
        parts = desc.split('@', 1)
        board_type = parts[0].strip()
        cut_dim = parts[1].strip()
        return {"quantity": qty, "dimensions": cut_dim, "description": board_type}
    else:
        return {"quantity": qty, "dimensions": "", "description": desc}

def detect_site_version(main_content):
    """Detect whether the page uses the OLD or NEW Ana White format."""
    # New format uses 'public-step' sections and h3 headings for lists
    if main_content.find(class_='public-step'):
        return 'new'
    # Old format uses 'field--name-field-shoppinglist' etc.
    if main_content.find(class_=lambda c: c and 'field--name-field-shoppinglist' in c):
        return 'old'
    # Check for new-style h3 headings
    for h3 in main_content.find_all('h3'):
        if h3.get_text(strip=True).lower() in ['shopping list', 'cut list']:
            return 'new'
    return 'old'  # Default fallback

def extract_list_after_heading(main_content, heading_text):
    """NEW FORMAT: Find an h3 heading and extract items from the next <pre> or <ul> sibling."""
    items = []
    for h3 in main_content.find_all('h3'):
        if heading_text.lower() in h3.get_text(strip=True).lower():
            ns = h3.find_next_sibling()
            while ns and ns.name not in ['h3', 'h2']:
                if ns.name == 'pre':
                    # <pre> tags contain newline-separated items
                    lines = ns.get_text(separator='\n').split('\n')
                    items.extend([l.strip() for l in lines if l.strip()])
                elif ns.name == 'ul':
                    items.extend([li.get_text(strip=True) for li in ns.find_all('li')])
                elif ns.name in ['p', 'div']:
                    text = ns.get_text(strip=True)
                    if text:
                        items.extend([l.strip() for l in text.split('\n') if l.strip()])
                ns = ns.find_next_sibling()
            break
    return items

def extract_list_by_class(main_content, class_keywords):
    """OLD FORMAT: Find items by CSS class name."""
    items = []
    fields = main_content.find_all(class_=lambda c: c and any(k in c.lower() for k in class_keywords))
    for field in fields:
        if 'field--name-field' in ' '.join(field.get('class', [])):
            items_container = field.find(class_='field--item') or field.find(class_='field--items')
            if items_container:
                all_lis = items_container.find_all('li')
                if all_lis:
                    items = [li.get_text(strip=True) for li in all_lis]
                else:
                    items = [line.strip() for line in items_container.get_text(separator='\n').split('\n') if line.strip()]
            break
    return items


def parse_ana_white_url(url, t_id):
    """
    Parses an Ana White URL. Supports both OLD and NEW website formats.
    Returns the JSON schema expected by generator.py.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    main_content = soup.find('main') or soup
    site_version = detect_site_version(main_content)
    print(f"Detected site version: {site_version}")
    
    # ========== 1. PROJECT TITLE ==========
    raw_title = soup.title.string if soup.title else ""
    project_title = clean_text(raw_title)
    if not project_title:
        h1 = main_content.find('h1')
        project_title = clean_text(h1.get_text(strip=True)) if h1 else "Woodworking Project"
        
    # ========== IMAGE DOWNLOADER ==========
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
                    if pil_img.mode != 'RGB':
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

    # ========== 2. HERO IMAGE ==========
    hero_image_source = None
    if site_version == 'new':
        hero_div = main_content.find(class_='plan-public-image')
        if hero_div:
            hero_image_source = download_image(hero_div.find('img'))
    
    if not hero_image_source:
        hero_field = main_content.find(class_='field--name-field-image')
        if hero_field:
            hero_image_source = download_image(hero_field.find('img'))
    
    if not hero_image_source:
        hero_image_source = download_image(main_content.find('img'))

    # ========== 3. DIMENSIONS ==========
    dimensions_str = ""
    dimension_image_source = None
    
    if site_version == 'new':
        dim_figure = main_content.find(class_='public-dimension-diagram')
        if dim_figure:
            dim_img = dim_figure.find('img')
            if dim_img:
                dimension_image_source = download_image(dim_img)
            dimensions_str = dim_figure.get_text(strip=True)
    else:
        dim_label = main_content.find(string=lambda t: t and "Dimensions" in t)
        if dim_label and dim_label.parent:
            dim_parent = dim_label.parent.parent
            dim_img = dim_parent.find('img')
            if dim_img:
                dimension_image_source = download_image(dim_img)
            else:
                ns = dim_parent.find_next_sibling()
                if ns:
                    dim_img2 = ns.find('img')
                    if dim_img2:
                        dimension_image_source = download_image(dim_img2)
                    dimensions_str = ns.get_text(separator=' ', strip=True)

    # ========== 4. SHOPPING LIST & CUT LIST ==========
    materials = []
    cut_list = []
    
    if site_version == 'new':
        raw_shopping = extract_list_after_heading(main_content, 'shopping list')
        # Also try "What to buy" heading
        if not raw_shopping:
            raw_shopping = extract_list_after_heading(main_content, 'what to buy')
        raw_cut = extract_list_after_heading(main_content, 'cut list')
    else:
        raw_shopping = extract_list_by_class(main_content, ['shoppinglist', 'materials', 'shopping-list'])
        raw_cut = extract_list_by_class(main_content, ['cutlist', 'cut-list', 'cut_list'])
        # Fallback for old format
        if not raw_cut:
            cut_fields = main_content.find_all(class_=lambda c: c and any(k in c.lower() for k in ['cutlist', 'cut-list', 'cut_list']))
            for field in cut_fields:
                if 'field--name-field' in ' '.join(field.get('class', [])):
                    items_container = field.find(class_='field--item') or field.find(class_='field--items')
                    if items_container:
                        all_lis = items_container.find_all('li')
                        if all_lis:
                            raw_cut = [li.get_text(strip=True) for li in all_lis]
                        else:
                            raw_cut = [line.strip() for line in items_container.get_text(separator='\n').split('\n') if line.strip()]
                    break
    
    for item in raw_shopping:
        qty, desc = parse_item_qty_desc(item)
        materials.append({"quantity": qty, "description": desc})
        
    for item in raw_cut:
        cut_list.append(parse_cut_item(item))

    # ========== 5. STEPS ==========
    steps = []
    
    if site_version == 'new':
        # New format: <section class="public-step"> containing h3, divs
        step_sections = main_content.find_all(class_='public-step')
        for i, section in enumerate(step_sections):
            step_title = f"Step {i + 1}"
            step_subtitle = ""
            step_desc = []
            step_images = []
            
            # Get title from h3
            h3 = section.find('h3')
            if h3:
                h3_text = h3.get_text(strip=True)
                # Some h3s are just "Step 3", others have the description
                if re.match(r'^Step\s*\d+$', h3_text):
                    step_title = h3_text
                else:
                    step_title = f"Step {i + 1}"
                    # Use a regex to strip "Step X " from the h3 text if it's there
                    clean_h3 = re.sub(r'^Step\s*\d+\s*', '', h3_text).strip()
                    step_subtitle = clean_h3
            
            # Get description from public-step-copy
            copy_div = section.find(class_='public-step-copy')
            if copy_div:
                # Get text but skip the h3 we already processed
                for child in copy_div.children:
                    if child.name == 'h3':
                        continue
                    text = child.get_text(strip=True) if hasattr(child, 'get_text') else str(child).strip()
                    if text:
                        # Remove redundant "StepN" or "Step N" from start of text
                        text = re.sub(r'^Step\s*\d+\s*', '', text).strip()
                        if text:
                            step_desc.append(text)
            
            # Get images from public-step-media
            media_div = section.find(class_='public-step-media')
            if media_div:
                for img in media_div.find_all('img'):
                    src = download_image(img)
                    if src:
                        step_images.append(src)
            
            steps.append({
                "step_number": i + 1,
                "title": step_title,
                "subtitle": step_subtitle,
                "exact_description": "\n".join(step_desc),
                "image_sources": step_images
            })
    else:
        # Old format: h2/h3/h4 with "step" in text
        def is_step_header(tag):
            text = tag.get_text(strip=True).lower()
            if 'step' not in text: return False
            if tag.name in ['h2', 'h3', 'h4']: return True
            if tag.name == 'p' and (tag.find('strong') or tag.find('b')):
                if text.startswith('step'): return True
            return False

        step_headers = main_content.find_all(is_step_header)
        
        for i, h in enumerate(step_headers):
            step_title = h.get_text(strip=True)
            step_desc = []
            step_images = []
            
            next_node = h.find_next_sibling()
            while next_node and not is_step_header(next_node):
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
                "subtitle": "",
                "exact_description": "\n".join(step_desc),
                "image_sources": step_images
            })

    # ========== 6. PROJECT OVERVIEW ==========
    intro_parts = []
    
    if site_version == 'new':
        summary_field = main_content.find(class_='field--name-field-summary')
        if summary_field:
            intro_parts.append(summary_field.get_text(separator='\n', strip=True))
        # New format may also have plan-public-summary
        plan_summary = main_content.find(class_='plan-public-summary')
        if plan_summary:
            intro_parts.append(plan_summary.get_text(separator='\n', strip=True))
    else:
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
            
    raw_intro = "\n\n".join(intro_parts)
    if raw_intro.lower().replace('\n', '').strip() == "add brag post":
        raw_intro = ""
    else:
        raw_intro = raw_intro.replace('Add Brag Post', '').strip()
        
    if raw_intro:
        summarized_intro = ai_summarize_overview(raw_intro)
        if len(summarized_intro) > 400:
            sentences = re.split(r'(?<=[.!?])\s+', summarized_intro)
            if len(sentences) > 4:
                summarized_intro = " ".join(sentences[:4])
            if len(summarized_intro) > 350:
                summarized_intro = summarized_intro[:347] + "..."
        project_intro = clean_text(summarized_intro)
    else:
        project_intro = ""

    # ========== 7. TOOLS ==========
    tools_list = []
    
    if site_version == 'new':
        # New format: tool grid with images after "Basic tools" h3
        tool_grid = main_content.find(class_='public-tool-grid')
        if tool_grid:
            for img in tool_grid.find_all('img'):
                alt = img.get('alt')
                if alt:
                    # Strip checkmarks and other symbols
                    clean_alt = re.sub(r'^[\u2713\u2714\u2716\u2022\s]+', '', alt).strip()
                    if clean_alt:
                        tools_list.append(clean_alt)
            # If no images with alt text, try text-based tool names
            if not tools_list:
                for item in tool_grid.find_all(['span', 'div', 'p', 'li']):
                    text = item.get_text(strip=True)
                    # Strip checkmarks
                    text = re.sub(r'^[\u2713\u2714\u2716\u2022\s]+', '', text).strip()
                    if text and len(text) < 50:
                        tools_list.append(text)
    else:
        tools_field = main_content.find(class_='field--name-field-tools')
        if tools_field:
            for img in tools_field.find_all('img'):
                alt = img.get('alt')
                if alt:
                    tools_list.append(alt)
                
    # ========== 8. FINISHING INSTRUCTIONS ==========
    finishing_instructions = []
    
    if site_version == 'new':
        # New format: after "How to Finish Your Project" h2
        for h2 in main_content.find_all('h2'):
            if 'finish' in h2.get_text(strip=True).lower():
                ns = h2.find_next_sibling()
                while ns and ns.name != 'h2':
                    text = ns.get_text(strip=True)
                    if text and 'instructions' not in text.lower():
                        finishing_instructions.append(text)
                    ns = ns.find_next_sibling()
                break
    else:
        prep_field = main_content.find(class_=lambda c: c and 'preparation' in c.lower())
        if prep_field:
            lines = prep_field.get_text(separator='\n').split('\n')
            finishing_instructions.extend([line.strip() for line in lines if line.strip() and "instructions" not in line.lower()])
            
        finish_field = main_content.find(class_=lambda c: c and 'finishing' in c.lower())
        if finish_field:
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
