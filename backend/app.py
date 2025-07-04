from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import uuid
import shutil
import zipfile
import time
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from datetime import datetime, timedelta
import subprocess
import tempfile
import threading
from fbx_processor import FBXProcessor
from utils import RateLimiter, SecurityValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../frontend')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fbx-to-mdl-converter-secret')

# Enable CORS for development
CORS(app)

# Setup proxy headers if behind reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Initialize rate limiter and security validator
rate_limiter = RateLimiter()
security_validator = SecurityValidator()

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Job tracking
jobs = {}

class ConversionJob:
    def __init__(self, job_id):
        self.job_id = job_id
        self.status = 'queued'  # queued, processing, completed, failed
        self.progress = 0
        self.log = []
        self.result_file = None
        self.error_message = None
        self.created_at = datetime.now()

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle FBX file upload and start conversion job"""
    try:
        # Get client IP for rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_ip):
            return jsonify({
                'error': 'Rate limit exceeded. Please wait before uploading again.'
            }), 429
        
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Security validation
        if not security_validator.validate_file(file):
            return jsonify({'error': 'Invalid file type or potentially malicious file'}), 400
        
        # Get optional parameters
        scale = request.form.get('scale', '1.0')
        bodygroup_name = request.form.get('bodygroup_name', 'default')
        
        try:
            scale = float(scale)
            if scale <= 0 or scale > 100:
                return jsonify({'error': 'Scale must be between 0 and 100'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid scale value'}), 400
        
        # Create job
        job_id = str(uuid.uuid4())
        job = ConversionJob(job_id)
        jobs[job_id] = job
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(upload_path)
        
        # Start conversion in background thread
        thread = threading.Thread(
            target=process_fbx_job,
            args=(job_id, upload_path, scale, bodygroup_name)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'message': 'File uploaded successfully. Processing started.'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error during upload'}), 500

def process_fbx_job(job_id, fbx_path, scale, bodygroup_name):
    """Process FBX file in background thread"""
    job = jobs[job_id]
    
    try:
        job.status = 'processing'
        job.log.append(f"Starting FBX processing for job {job_id}")
        
        # Initialize processor
        processor = FBXProcessor()
        
        # Create output directory for this job
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Process the FBX file
        def progress_callback(progress, message):
            job.progress = progress
            job.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        result = processor.convert_fbx_to_mdl(
            fbx_path, 
            output_dir, 
            scale=scale,
            bodygroup_name=bodygroup_name,
            progress_callback=progress_callback
        )
        
        if result['success']:
            # Create ZIP file with results
            zip_path = os.path.join(output_dir, f"{job_id}_result.zip")
            create_result_zip(result['files'], zip_path, fbx_path)
            
            job.status = 'completed'
            job.result_file = zip_path
            job.progress = 100
            job.log.append("Conversion completed successfully!")
        else:
            job.status = 'failed'
            job.error_message = result.get('error', 'Unknown error occurred')
            job.log.append(f"Conversion failed: {job.error_message}")
    
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.log.append(f"Error: {str(e)}")
        logger.error(f"Job {job_id} failed: {str(e)}")
    
    finally:
        # Clean up uploaded file
        try:
            if os.path.exists(fbx_path):
                os.remove(fbx_path)
        except Exception as e:
            logger.warning(f"Failed to clean up uploaded file: {str(e)}")

def create_result_zip(result_files, zip_path, original_fbx_path):
    """Create ZIP file with conversion results"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add result files
        for file_path in result_files:
            if os.path.exists(file_path):
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
        
        # Add original FBX file
        if os.path.exists(original_fbx_path):
            zipf.write(original_fbx_path, f"original_{os.path.basename(original_fbx_path)}")

@app.route('/status/<job_id>')
def get_job_status(job_id):
    """Get job status and progress"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    # Clean up old completed/failed jobs
    if job.status in ['completed', 'failed']:
        time_limit = datetime.now() - timedelta(hours=1)
        if job.created_at < time_limit:
            cleanup_job(job_id)
            return jsonify({'error': 'Job expired'}), 404
    
    return jsonify({
        'job_id': job_id,
        'status': job.status,
        'progress': job.progress,
        'log': job.log[-10:],  # Return last 10 log entries
        'error': job.error_message,
        'has_result': job.result_file is not None
    })

@app.route('/download/<job_id>')
def download_result(job_id):
    """Download conversion result ZIP file"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    if job.status != 'completed' or not job.result_file:
        return jsonify({'error': 'No result available'}), 404
    
    if not os.path.exists(job.result_file):
        return jsonify({'error': 'Result file not found'}), 404
    
    return send_file(
        job.result_file,
        as_attachment=True,
        download_name=f"converted_model_{job_id}.zip",
        mimetype='application/zip'
    )

def cleanup_job(job_id):
    """Clean up job files and data"""
    if job_id in jobs:
        job = jobs[job_id]
        
        # Remove output directory
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)
        
        # Remove job from memory
        del jobs[job_id]

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'active_jobs': len([j for j in jobs.values() if j.status == 'processing']),
        'total_jobs': len(jobs)
    })

# Cleanup old jobs periodically
def cleanup_old_jobs():
    """Clean up jobs older than 1 hour"""
    while True:
        try:
            time.sleep(300)  # Check every 5 minutes
            current_time = datetime.now()
            jobs_to_remove = []
            
            for job_id, job in jobs.items():
                if current_time - job.created_at > timedelta(hours=1):
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                cleanup_job(job_id)
                
        except Exception as e:
            logger.error(f"Error in cleanup thread: {str(e)}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_jobs)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)