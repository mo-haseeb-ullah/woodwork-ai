import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO

def scrape_images_from_url(url):
    """
    Scrapes a woodworking blog post URL.
    Returns (scraped_images, scraped_text)
    """
    scraped_images = []
    scraped_text = ""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- 1. Extract Text ---
        # Find main content area to avoid sidebar/footer ads
        main_content = soup.find('div', class_='entry-content') or \
                       soup.find('div', class_='post-content') or \
                       soup.find('article') or \
                       soup.find('main') or \
                       soup
                       
        # Extract headings, paragraphs, and list items from MAIN content
        text_elements = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li'])
        lines = []
        for el in text_elements:
            text = el.get_text(separator=' ', strip=True)
            if text and len(text) > 10:  # ignore tiny meaningless elements
                lines.append(text)
        scraped_text = "\n".join(lines)
        
        # --- 2. Extract Images ---
        # Only extract images from the MAIN content to avoid 50+ ad pictures!
        img_tags = main_content.find_all('img')
        
        save_dir = "scraped_images"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # Optional: Clean old scraped images so they don't pile up
        for old_f in os.listdir(save_dir):
            try:
                os.remove(os.path.join(save_dir, old_f))
            except:
                pass
                
        for i, img in enumerate(img_tags):
            # Prioritize lazy-loaded data attributes over the default 'src' (which is often a placeholder)
            img_url = img.get('data-lazy-src') or img.get('data-src') or img.get('src')
            if not img_url:
                continue
                
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                parsed_url = urlparse(url)
                img_url = f"{parsed_url.scheme}://{parsed_url.netloc}{img_url}"
                
            try:
                # Use a strict tuple timeout (5s connect, 15s read) to prevent 72-minute hangs
                img_res = requests.get(img_url, headers=headers, timeout=(5, 15))
                if img_res.status_code == 200:
                    with Image.open(BytesIO(img_res.content)) as pil_img:
                        if pil_img.width < 250 or pil_img.height < 250:
                            continue
                            
                        # Convert EVERYTHING to JPEG for maximum compatibility
                        if pil_img.mode in ('RGBA', 'P', 'LA'):
                            pil_img = pil_img.convert('RGB')
                        elif pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                            
                        filename = f"scraped_{i}.jpg"
                        filepath = os.path.join(save_dir, filename)
                        pil_img.save(filepath, format='JPEG', quality=85)
                                
                        scraped_images.append(filepath)
            except Exception as e:
                print(f"Skipping image {img_url}: {e}")
                continue
                
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch website: {e}")
    except Exception as e:
        raise Exception(f"Error extracting content: {e}")
        
    return scraped_images, scraped_text

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        scrape_images_from_url(sys.argv[1])
