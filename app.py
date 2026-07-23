from flask import Flask, render_template, request, send_file, jsonify
import os
import json

# Fix for protobuf issue on Python 3.14
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from ai_processor import process_with_ai
from generator import generate_premium_pdf # generates docx now
from scraper import scrape_images_from_url

import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("GEMINI_API_KEY", "")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB max limit

@app.route('/')
def index():
    return render_template('index.html')

import uuid
import threading
import traceback

tasks = {}

@app.route('/process', methods=['POST'])
def process():
    project_url = request.form.get('url')
    if not project_url:
        return jsonify({'error': 'No URL provided'}), 400
        
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing'}
    
    def run_task(t_id, url):
        try:
            # Step 1: Scrape Images and Text from URL
            scraped_images, scraped_text = scrape_images_from_url(url)
            
            if not scraped_text:
                tasks[t_id] = {'status': 'error', 'error': 'Could not extract text from the provided URL.'}
                return
                
            # Step 2: AI Processing
            json_output = process_with_ai(scraped_text, API_KEY, scraped_images)
            
            with open(f"raw_output_{t_id}.json", "w", encoding='utf-8') as f:
                f.write(json_output)
                
            # Step 3: Generate Output
            output_filename = f"Premium_Plan_{t_id}.docx"
            generate_premium_pdf(json_output, {}, {}, output_filename)
            
            tasks[t_id] = {'status': 'completed', 'docx': output_filename}
            
        except Exception as e:
            traceback.print_exc()
            tasks[t_id] = {'status': 'error', 'error': str(e)}

    threading.Thread(target=run_task, args=(task_id, project_url)).start()
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
    if not task or task['status'] != 'completed':
        return "File not ready", 400
    return send_file(task['docx'], as_attachment=True, download_name="Premium_Plan.docx")
        
if __name__ == '__main__':
    # Ensure templates and static folders exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
