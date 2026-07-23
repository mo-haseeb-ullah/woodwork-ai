import json
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def insert_hr(paragraph):
    """Inserts a horizontal rule (border) under a paragraph."""
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)

def generate_premium_pdf(plan_json_str, page_to_images=None, docx_images_dict=None, output_filename="Premium_Plan.docx"):
    """
    Despite the name `generate_premium_pdf`, this now generates a DOCX file.
    Keeping the function signature identical for compatibility with app.py.
    """
    plan_data = json.loads(plan_json_str)
    project_name = plan_data.get("project_name", "Woodworking Plan")

    doc = Document()

    def add_heading(text, level=2):
        if level == 1:
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.bold = True
            run.font.size = Pt(22)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            insert_hr(p)
        else:
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.bold = True
            run.font.size = Pt(16)
            insert_hr(p)

    def add_bullet(text):
        doc.add_paragraph(text, style='List Bullet')

    def embed_image_if_exists(image_source, target_width_inches=6.0):
        if not image_source or not isinstance(image_source, str) or not image_source.startswith("scraped_"):
            return False
            
        scraped_dir = "scraped_images"
        if os.path.exists(scraped_dir):
            for f in os.listdir(scraped_dir):
                if f.startswith(image_source + ".") or f == image_source:
                    try:
                        img_path = os.path.join(scraped_dir, f)
                        p = doc.add_paragraph()
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        run = p.add_run()
                        run.add_picture(img_path, width=Inches(target_width_inches))
                        return True
                    except Exception as e:
                        print(f"Failed to embed image {img_path}: {e}")
        return False

    # --- 1. TITLE & HERO ---
    add_heading(project_name, level=1)
    
    diff_text = plan_data.get("difficulty_level", "DIY Project")
    p_diff = doc.add_paragraph(f"Difficulty: {diff_text}")
    p_diff.alignment = WD_ALIGN_PARAGRAPH.CENTER

    embed_image_if_exists(plan_data.get("hero_image_source"))

    # --- 2. INTRO BOX ---
    if plan_data.get("project_intro"):
        p_intro = doc.add_paragraph()
        run = p_intro.add_run(plan_data["project_intro"])
        run.italic = True
        doc.add_paragraph() # Spacer

    # --- 3. DIMENSIONS ---
    if plan_data.get("finished_dimensions"):
        p_dim = doc.add_paragraph()
        p_dim.add_run("Dimensions: ").bold = True
        p_dim.add_run(plan_data['finished_dimensions'])

    dim_page = plan_data.get("dimension_image_source")
    if dim_page:
        add_heading("Dimensions")
        embed_image_if_exists(dim_page)
    
    # --- 4. SHOPPING LIST (MATERIALS) ---
    if plan_data.get("materials"):
        add_heading("Shopping List")
        for material in plan_data.get("materials", []):
            qty = material.get("quantity", "")
            desc = material.get("description", "")
            if qty:
                add_bullet(f"{qty} — {desc}")
            else:
                add_bullet(desc)
        doc.add_paragraph()

    # --- 5. CUT LIST ---
    if plan_data.get("cut_list"):
        add_heading("Cut List")
        for cut in plan_data.get("cut_list", []):
            add_bullet(f"{cut['quantity']} — {cut['dimensions']} — {cut['description']}")
        doc.add_paragraph()

    # --- 6. TOOLS ---
    if plan_data.get("tools"):
        add_heading("Tools")
        
        tools_page = plan_data.get("tools_image_source")
        if tools_page:
             embed_image_if_exists(tools_page)

        for tool in plan_data.get("tools", []):
            add_bullet(tool['name'])
        doc.add_paragraph()
    
    # --- 7. CONSTRUCTION STEPS ---
    if plan_data.get("steps"):
        for step in plan_data.get("steps", []):
            doc.add_page_break()
            
            # Step Banner
            step_num = step.get('step_number', '')
            step_title = step.get('title', '')
            add_heading(f"STEP {step_num}: {step_title}")
            
            embed_image_if_exists(step.get("image_source"))
            
            # Instructions Box
            for inst in step.get("instructions", []):
                add_bullet(inst)

    doc.save(output_filename)
    print(f"Generated {output_filename}")
