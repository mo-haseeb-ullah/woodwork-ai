from flask import Flask, render_template, request, send_file, jsonify
import os
import json
import uuid
import threading
import traceback
from werkzeug.utils import secure_filename

# Fix for protobuf issue on Python 3.14
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from ai_processor import process_with_ai
from generator import generate_premium_pdf
from scraper import scrape_images_from_url
from pdf_extractor import extract_from_pdf, create_images_zip

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("GEMINI_API_KEY", "")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB max limit
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

tasks = {}

@app.route('/process', methods=['POST'])
def process():
    project_url = request.form.get('url')
    pdf_file = request.files.get('pdf_file')
    
    if not project_url and not pdf_file:
        return jsonify({'error': 'Please provide either a Blog URL or upload a PDF file.'}), 400
        
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing'}
    
    def run_task(t_id, url=None, pdf_filepath=None):
        try:
            custom_img_dir = None
            zip_filename = None
            
            if pdf_filepath:
                # PDF Processing Mode
                pdf_img_dir = os.path.join("extracted_images", f"pdf_{t_id}")
                scraped_images, scraped_text = extract_from_pdf(pdf_filepath, pdf_img_dir)
                custom_img_dir = pdf_img_dir
                
                if not scraped_text.strip():
                    tasks[t_id] = {'status': 'error', 'error': 'Could not extract text from the provided PDF file.'}
                    return
                    
                # Build ZIP file containing extracted images
                if scraped_images:
                    zip_filename = f"PDF_Images_{t_id}.zip"
                    create_images_zip(scraped_images, zip_filename)
            else:
                # URL Scraping Mode
                scraped_images, scraped_text = scrape_images_from_url(url)
                if not scraped_text:
                    tasks[t_id] = {'status': 'error', 'error': 'Could not extract text from the provided URL.'}
                    return
                    
                if scraped_images:
                    zip_filename = f"Plan_Images_{t_id}.zip"
                    create_images_zip(scraped_images, zip_filename)
                
            # Step 2: AI Processing (without skipping steps/branding removal)
            json_output = process_with_ai(scraped_text, API_KEY, scraped_images)
            
            with open(f"raw_output_{t_id}.json", "w", encoding='utf-8') as f:
                f.write(json_output)
                
            # Step 3: Generate Output DOCX
            output_filename = f"Premium_Plan_{t_id}.docx"
            generate_premium_pdf(json_output, {}, {}, output_filename, custom_img_dir=custom_img_dir)
            
            task_result = {
                'status': 'completed', 
                'docx': output_filename,
                'has_zip': bool(zip_filename and os.path.exists(zip_filename))
            }
            if zip_filename and os.path.exists(zip_filename):
                task_result['zip'] = zip_filename
                
            tasks[t_id] = task_result
            
            # Clean up temporary uploaded PDF
            if pdf_filepath and os.path.exists(pdf_filepath):
                try:
                    os.remove(pdf_filepath)
                except Exception:
                    pass
            
        except Exception as e:
            traceback.print_exc()
            tasks[t_id] = {'status': 'error', 'error': str(e)}

    # Check request type
    if pdf_file and pdf_file.filename:
        filename = secure_filename(pdf_file.filename)
        saved_pdf_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
        pdf_file.save(saved_pdf_path)
        threading.Thread(target=run_task, kwargs={'t_id': task_id, 'pdf_filepath': saved_pdf_path}).start()
    else:
        threading.Thread(target=run_task, kwargs={'t_id': task_id, 'url': project_url}).start()
        
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'not_found'}), 404
    return jsonify(task)

@app.route('/download/<task_id>', methods=['GET'])
def download(task_id):
    task = tasks.get(task_id)
    if not task or task['status'] != 'completed' or 'docx' not in task:
        return "File not ready", 400
    return send_file(task['docx'], as_attachment=True, download_name="Premium_Plan.docx")

@app.route('/download_zip/<task_id>', methods=['GET'])
def download_zip(task_id):
    task = tasks.get(task_id)
    if not task or task['status'] != 'completed' or 'zip' not in task:
        return "ZIP File not ready", 400
    return send_file(task['zip'], as_attachment=True, download_name="Plan_Images.zip")
        
if __name__ == '__main__':
    # Ensure required folders exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('extracted_images', exist_ok=True)
    app.run(debug=True, port=5000)

