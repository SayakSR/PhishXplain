from flask import Flask, request, jsonify, send_file, Response, send_from_directory
from flask_cors import CORS
import subprocess
import os
import json
import time
import logging
import threading
import sys
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/analyze": {"origins": ["chrome-extension://*"]},
    r"/landing": {"origins": ["chrome-extension://*"]},
    r"/progress/*": {"origins": ["chrome-extension://*"]},
    r"/images/*": {"origins": ["chrome-extension://*"]},
    r"/warning": {"origins": ["chrome-extension://*"]},
    r"/priority": {"origins": ["chrome-extension://*"]}
})

# Get the absolute path to the extension directory
EXTENSION_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(os.path.dirname(EXTENSION_DIR), 'artifacts')
IMAGES_DIR = os.path.join(EXTENSION_DIR, 'images')

# Get the Python executable path
PYTHON_EXECUTABLE = sys.executable
logger.info(f"Using Python executable: {PYTHON_EXECUTABLE}")

# Store progress for each analysis
analysis_progress = {}

def copy_generated_files():
    """Copy generated files from artifacts to extension directory"""
    try:
        # Copy warning.html
        warning_src = os.path.join(ARTIFACTS_DIR, 'warning.html')
        warning_dst = os.path.join(EXTENSION_DIR, 'warning.html')
        if os.path.exists(warning_src):
            shutil.copy2(warning_src, warning_dst)
            logger.info(f"Copied warning.html to {warning_dst}")

        # Copy screenshot
        screenshot_src = os.path.join(ARTIFACTS_DIR, 'website_screenshot_with_boxes.png')
        screenshot_dst = os.path.join(IMAGES_DIR, 'website_screenshot_with_boxes.png')
        if os.path.exists(screenshot_src):
            shutil.copy2(screenshot_src, screenshot_dst)
            logger.info(f"Copied screenshot to {screenshot_dst}")

    except Exception as e:
        logger.error(f"Error copying files: {e}")
        raise

@app.route('/images/<path:filename>')
def serve_image(filename):
    try:
        logger.info(f"Serving image: {filename} from {IMAGES_DIR}")
        return send_from_directory(IMAGES_DIR, filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return jsonify({'error': str(e)}), 404

def update_progress(analysis_id, stage):
    analysis_progress[analysis_id] = stage

def run_script(script_name, *args):
    script_path = os.path.join(os.path.dirname(EXTENSION_DIR), script_name)
    logger.info(f"Running script: {script_path} with args: {args}")
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    process = subprocess.Popen(
        [PYTHON_EXECUTABLE, script_path] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(EXTENSION_DIR)
    )
    stdout, stderr = process.communicate()
    
    if stderr:
        logger.error(f"{script_name} stderr: {stderr.decode()}")
    
    if stdout:
        logger.info(f"{script_name} stdout: {stdout.decode()}")
    
    if process.returncode != 0:
        raise Exception(f"{script_name} failed with return code {process.returncode}")
    
    return stdout, stderr

def analyze_url_thread(url, analysis_id):
    try:
        update_progress(analysis_id, 'get')
        # Run get.py with URL as argument
        run_script('get.py', url)

        # Check if get.py generated required files
        screenshot_path = os.path.join(ARTIFACTS_DIR, 'website_screenshot.png')
        text_path = os.path.join(ARTIFACTS_DIR, 'website_text_coordinates.json')
        if not os.path.exists(screenshot_path) or not os.path.exists(text_path):
            error_msg = "get.py failed to generate required files"
            logger.error(error_msg)
            raise Exception(error_msg)

        update_progress(analysis_id, 'generate')
        # Run generate.py
        run_script('generate.py')

        # Check if generate.py generated required files
        priority_path = os.path.join(ARTIFACTS_DIR, 'highest_priority_elements.json')
        if not os.path.exists(priority_path):
            error_msg = "generate.py failed to generate required files"
            logger.error(error_msg)
            raise Exception(error_msg)

        update_progress(analysis_id, 'annotate')
        # Run annotate.py
        run_script('annotate.py')

        # Check if annotate.py generated required files
        warning_path = os.path.join(ARTIFACTS_DIR, 'warning.html')
        if not os.path.exists(warning_path):
            error_msg = "annotate.py failed to generate required files"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Copy generated files to extension directory
        copy_generated_files()

        update_progress(analysis_id, 'complete')
    except Exception as e:
        logger.exception("Error in analysis thread")
        update_progress(analysis_id, 'error')
        # Store the error message for the client
        analysis_progress[f"{analysis_id}_error"] = str(e)

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_url():
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            logger.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400

        logger.info(f"Analyzing URL: {url}")
        
        # Generate a unique ID for this analysis
        analysis_id = str(time.time())
        analysis_progress[analysis_id] = 'started'
        
        # Start analysis in a separate thread
        thread = threading.Thread(
            target=analyze_url_thread,
            args=(url, analysis_id)
        )
        thread.start()
        
        return jsonify({'analysis_id': analysis_id})
            
    except Exception as e:
        logger.exception("Error in analyze_url")
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<analysis_id>')
def get_progress(analysis_id):
    def generate():
        while True:
            stage = analysis_progress.get(analysis_id, 'error')
            error_msg = analysis_progress.get(f"{analysis_id}_error", None)
            
            logger.info(f"Progress update for {analysis_id}: {stage}")
            
            if stage in ['complete', 'error']:
                logger.info(f"Final stage for {analysis_id}: {stage}")
                yield f"data: {json.dumps({'stage': stage, 'error': error_msg})}\n\n"
                break
            yield f"data: {json.dumps({'stage': stage, 'error': error_msg})}\n\n"
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/landing')
def landing():
    landing_path = os.path.join(EXTENSION_DIR, 'landing.html')
    logger.info(f"Serving landing page from: {landing_path}")
    return send_file(landing_path)

@app.route('/warning')
def warning():
    warning_path = os.path.join(EXTENSION_DIR, 'warning.html')
    logger.info(f"Serving warning page from: {warning_path}")
    return send_file(warning_path)

@app.route('/priority')
def get_priority():
    try:
        priority_path = os.path.join(ARTIFACTS_DIR, 'highest_priority_elements.json')
        logger.info(f"Reading priority data from: {priority_path}")
        
        if not os.path.exists(priority_path):
            logger.error(f"Priority file not found: {priority_path}")
            return jsonify({'error': 'Priority data not found'}), 404
            
        with open(priority_path, 'r') as f:
            priority_data = json.load(f)
            logger.info(f"Successfully loaded priority data: {priority_data}")
            return jsonify(priority_data)
    except Exception as e:
        logger.error(f"Error reading priority data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/screenshot')
def get_screenshot():
    return send_file('images/website_screenshot_with_boxes.png', mimetype='image/png')

if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(host='127.0.0.1', port=5000) 